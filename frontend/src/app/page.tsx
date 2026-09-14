'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Droplet,
  Heart,
  Search,
  Shield,
  Clock,
  MapPin,
  CheckCircle2,
  ArrowRight,
  UserCheck,
  AlertCircle,
  AlertTriangle,
  PhoneCall,
  Activity,
  Phone,
  KeyRound,
  Loader2,
  Lock,
} from 'lucide-react';
import { BloodGroup, LocationItem } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'];

const DEFAULT_LOCATIONS: LocationItem[] = [
  { id: 1, name: 'Coimbatore', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 2, name: 'Sulur', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 3, name: 'Tiruppur', district: 'Tiruppur', state: 'Tamil Nadu', is_active: true },
  { id: 4, name: 'Pollachi', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 5, name: 'Mettupalayam', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 6, name: 'Avinashi', district: 'Tiruppur', state: 'Tamil Nadu', is_active: true },
  { id: 7, name: 'Palladam', district: 'Tiruppur', state: 'Tamil Nadu', is_active: true },
  { id: 8, name: 'Udumalpet', district: 'Tiruppur', state: 'Tamil Nadu', is_active: true },
  { id: 9, name: 'Annur', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 10, name: 'Madukkarai', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
  { id: 11, name: 'Perur', district: 'Coimbatore', state: 'Tamil Nadu', is_active: true },
];

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user, donorProfile, login } = useAuth();

  const [locations, setLocations] = useState<LocationItem[]>(DEFAULT_LOCATIONS);
  const [selectedGroup, setSelectedGroup] = useState<BloodGroup | ''>('');
  const [locationQuery, setLocationQuery] = useState<string>('');
  const [hasAcknowledgedDisclaimer, setHasAcknowledgedDisclaimer] = useState<boolean>(false);
  const [stats, setStats] = useState({
    total_donors: 148,
    available_donors: 112,
    total_locations: 11,
    avg_response_mins: 15,
  });

  // Inline Login state for Find a Donor frame
  const [loginStep, setLoginStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [loginName, setLoginName] = useState('');
  const [loginMobile, setLoginMobile] = useState('');
  const [loginOtp, setLoginOtp] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginCooldown, setLoginCooldown] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (loginCooldown > 0) {
      timer = setTimeout(() => setLoginCooldown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [loginCooldown]);

  useEffect(() => {
    api.getLocations().then((data) => {
      if (data && data.length > 0) {
        setLocations(data);
      }
    }).catch(() => {
      setLocations(DEFAULT_LOCATIONS);
    });

    api.getAdminStats().then((res) => {
      if (res && res.total_donors) {
        setStats({
          total_donors: res.total_donors || 148,
          available_donors: res.available_donors || 112,
          total_locations: 11,
          avg_response_mins: 15,
        });
      }
    }).catch(() => {});
  }, []);

  const normalizePhone = (num: string) => {
    const cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return `+91${cleaned}`;
    if (cleaned.length === 12 && cleaned.startsWith('91')) return `+${cleaned}`;
    if (num.startsWith('+91') && cleaned.length === 12) return num;
    return `+91${cleaned}`;
  };

  const handleInlineSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);

    const formatted = normalizePhone(loginMobile);
    if (!/^\+91[6-9]\d{9}$/.test(formatted)) {
      setLoginError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setLoginLoading(true);
    try {
      const res = await api.sendOtp(formatted, 'LOGIN');
      setLoginStep('OTP');
      setLoginCooldown(res.cooldown_seconds || 60);
    } catch (err: any) {
      setLoginError(err.message || 'Failed to send OTP.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleInlineVerifyLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);

    if (loginOtp.trim().length !== 6) {
      setLoginError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoginLoading(true);
    try {
      const formatted = normalizePhone(loginMobile);
      await login(formatted, loginOtp.trim());
      setLoginStep('PHONE');
    } catch (err: any) {
      setLoginError(err.message || 'Invalid or expired OTP.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleSearchDonors = (e: React.FormEvent) => {
    e.preventDefault();
    const query = new URLSearchParams();
    if (selectedGroup) query.append('blood_group', selectedGroup);
    if (locationQuery.trim()) query.append('location', locationQuery.trim());
    router.push(`/find-donor?${query.toString()}`);
  };

  return (
    <div className="flex flex-col min-h-full">
      {/* ================= HERO & CHOOSE YOUR PURPOSE ================= */}
      <section className="relative overflow-hidden bg-gradient-to-b from-red-50/80 via-white to-slate-50 pt-10 pb-16 md:pt-14 md:pb-20 border-b border-slate-200/70">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.7))] -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Main Title & Slogan */}
          <div className="text-center max-w-3xl mx-auto space-y-3 mb-10 md:mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-100/80 text-red-700 text-xs font-bold uppercase tracking-wider">
              <Droplet className="w-3.5 h-3.5 fill-red-600 text-red-600" />
              <span>Emergency Blood Matching Initiative</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15] uppercase">
              BLOOD CONNECT
            </h1>
            <p className="text-xl sm:text-2xl font-bold text-red-600">
              Connecting Donors. Saving Lives.
            </p>
            <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium max-w-2xl mx-auto">
              A platform that helps connect registered blood donors with people seeking blood based on blood group and location.
            </p>
          </div>

          {/* Choose Your Purpose Dual Cards */}
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-2xl sm:text-3xl font-black text-slate-900">
                Choose Your Purpose
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Select between voluntary donor registration and finding blood donors near you.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
              {/* Card 1: Register as a Donor */}
              <div className="bg-white rounded-3xl p-7 md:p-9 border-2 border-red-100 shadow-xl shadow-red-500/5 flex flex-col justify-between hover:border-red-300 transition-all">
                <div className="space-y-6">
                  <div className="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center text-red-600">
                    <Heart className="w-8 h-8 fill-red-600" />
                  </div>

                  <div>
                    <h3 className="text-2xl font-black text-slate-900">
                      Register as a Donor
                    </h3>
                    <p className="text-base font-bold text-slate-800 mt-2">
                      Want to donate blood?
                    </p>
                    <p className="text-sm text-slate-600 leading-relaxed mt-1">
                      Register your details and become part of the Blood Connect voluntary donor network.
                    </p>
                  </div>

                  {/* Benefits */}
                  <div className="space-y-2.5 pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>Voluntary, confidential, and safe registration</span>
                    </div>
                    <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>Receive emergency blood requests in your locality</span>
                    </div>
                    <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>Toggle your availability status anytime</span>
                    </div>
                  </div>
                </div>

                <div className="pt-6 mt-6 border-t border-slate-100">
                  <Link
                    href="/register"
                    className="w-full py-4 px-6 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-black text-base rounded-2xl shadow-lg shadow-red-600/25 hover:shadow-xl hover:shadow-red-600/30 transition-all flex items-center justify-center gap-3 cursor-pointer group"
                  >
                    <Heart className="w-5 h-5 fill-white" />
                    <span>REGISTER AS DONOR</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>
              </div>

              {/* Card 2: Find a Donor (With Embedded Simple Login) */}
              <div className="bg-white rounded-3xl p-7 md:p-9 border-2 border-slate-200 shadow-xl shadow-slate-200/60 flex flex-col justify-between hover:border-slate-300 transition-all">
                <div className="space-y-5">
                  <div className="w-14 h-14 bg-slate-900 rounded-2xl flex items-center justify-center text-white">
                    <Search className="w-7 h-7 text-rose-400" />
                  </div>

                  <div>
                    <h3 className="text-2xl font-black text-slate-900">
                      Find a Donor
                    </h3>
                    <p className="text-base font-bold text-slate-800 mt-2">
                      Need blood?
                    </p>
                    <p className="text-sm text-slate-600 leading-relaxed mt-1">
                      {isAuthenticated
                        ? 'Select blood group and location to search active donors.'
                        : 'Please log in below to select details and find verified donors.'}
                    </p>
                  </div>

                  {/* IF USER IS NOT AUTHENTICATED: EMBEDDED SIMPLE LOGIN FORM */}
                  {!isAuthenticated ? (
                    <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-4">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
                        <Lock className="w-4 h-4 text-red-600" />
                        <span>Sign In with Mobile OTP</span>
                      </div>

                      {loginError && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs text-red-700">
                          <AlertCircle className="w-4 h-4 flex-shrink-0" />
                          <span>{loginError}</span>
                        </div>
                      )}

                      {loginStep === 'PHONE' ? (
                        <form onSubmit={handleInlineSendOtp} className="space-y-3">
                          <div>
                            <label className="block text-xs font-semibold text-slate-600 mb-1">
                              Your Name (Optional)
                            </label>
                            <input
                              type="text"
                              placeholder="e.g. Ramesh Kumar"
                              value={loginName}
                              onChange={(e) => setLoginName(e.target.value)}
                              className="w-full px-3.5 py-2.5 bg-white text-xs border border-slate-300 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-bold text-slate-700 mb-1">
                              Mobile Number *
                            </label>
                            <div className="relative">
                              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500">
                                +91
                              </span>
                              <input
                                type="tel"
                                maxLength={10}
                                placeholder="9876543210"
                                value={loginMobile.replace(/^\+91/, '')}
                                onChange={(e) => setLoginMobile(e.target.value.replace(/\D/g, ''))}
                                required
                                className="w-full pl-12 pr-3.5 py-2.5 bg-white text-xs border border-slate-300 rounded-xl font-bold text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                              />
                            </div>
                          </div>

                          <button
                            type="submit"
                            disabled={loginLoading}
                            className="w-full py-3 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                          >
                            {loginLoading ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Sending OTP...</span>
                              </>
                            ) : (
                              <>
                                <span>Continue with Mobile OTP</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </>
                            )}
                          </button>
                        </form>
                      ) : (
                        <form onSubmit={handleInlineVerifyLogin} className="space-y-3">
                          <div className="flex items-center justify-between text-xs text-slate-600">
                            <span>Code sent to: <strong>+91 {loginMobile.slice(-10)}</strong></span>
                            <button
                              type="button"
                              onClick={() => setLoginStep('PHONE')}
                              className="text-red-600 font-bold hover:underline cursor-pointer"
                            >
                              Change
                            </button>
                          </div>

                          <div>
                            <label className="block text-xs font-bold text-slate-700 mb-1">
                              6-Digit OTP *
                            </label>
                            <div className="relative">
                              <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                              <input
                                type="text"
                                maxLength={6}
                                placeholder="123456"
                                value={loginOtp}
                                onChange={(e) => setLoginOtp(e.target.value.replace(/\D/g, ''))}
                                required
                                autoFocus
                                className="w-full pl-10 pr-3.5 py-2.5 bg-white text-sm tracking-widest font-black text-slate-900 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden text-center"
                              />
                            </div>
                            <p className="text-[11px] text-slate-500 mt-1">
                              💡 Demo Mode: Enter any 6-digit code or <code className="bg-slate-200 px-1 py-0.5 rounded font-mono">123456</code>
                            </p>
                          </div>

                          <button
                            type="submit"
                            disabled={loginLoading}
                            className="w-full py-3 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                          >
                            {loginLoading ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Verifying OTP...</span>
                              </>
                            ) : (
                              <>
                                <CheckCircle2 className="w-4 h-4" />
                                <span>Verify & Unlock Search</span>
                              </>
                            )}
                          </button>
                        </form>
                      )}
                    </div>
                  ) : (
                    /* IF USER IS AUTHENTICATED: SHOW SEARCH DETAILS DIRECTLY */
                    <form onSubmit={handleSearchDonors} className="space-y-4 pt-1">
                      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800 font-semibold">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>Logged in as <strong>{donorProfile?.full_name || user?.mobile_number}</strong></span>
                        </div>
                        <span className="text-[10px] bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded-full font-bold">
                          {user?.role}
                        </span>
                      </div>

                      {/* Blood Group Selector */}
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                          Select Blood Group:
                        </label>
                        <div className="grid grid-cols-4 gap-2">
                          {BLOOD_GROUPS.map((bg) => (
                            <button
                              key={bg}
                              type="button"
                              onClick={() => setSelectedGroup(selectedGroup === bg ? '' : bg)}
                              className={`py-2 px-1 rounded-xl font-bold text-xs transition-all border text-center cursor-pointer ${
                                selectedGroup === bg
                                  ? 'bg-red-600 text-white border-red-600 shadow-md shadow-red-500/20'
                                  : 'bg-slate-50 hover:bg-red-50 text-slate-800 border-slate-200 hover:border-red-200'
                              }`}
                            >
                              {bg}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Location Selector */}
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                          Select Location:
                        </label>
                        <div className="relative">
                          <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                          <select
                            value={locationQuery}
                            onChange={(e) => setLocationQuery(e.target.value)}
                            className="w-full pl-10 pr-8 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all cursor-pointer"
                          >
                            <option value="">All 11 Regions (Tamil Nadu)</option>
                            {locations.map((loc) => (
                              <option key={loc.id} value={loc.name}>
                                {loc.name} ({loc.district})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <button
                        type="submit"
                        className="w-full py-3.5 px-6 bg-slate-900 hover:bg-black text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                      >
                        <Search className="w-4 h-4 text-rose-400" />
                        <span>SEARCH DONORS</span>
                      </button>
                    </form>
                  )}
                </div>

                {!isAuthenticated && (
                  <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Already registered?</span>
                    <Link href="/login" className="text-red-600 font-bold hover:underline cursor-pointer">
                      Sign In &rarr;
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= ABOUT OUR INITIATIVE & IMPORTANT NOTE ================= */}
      <section id="about-initiative" className="py-16 md:py-20 bg-white border-b border-slate-200/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="space-y-4">
            <span className="text-xs font-bold uppercase tracking-widest text-red-600">
              About Our Initiative
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900">
              What is Blood Connect?
            </h2>
            <p className="text-base text-slate-700 leading-relaxed font-normal">
              Blood Connect is a student-led social initiative designed to make finding blood donors easier and faster. The platform connects registered blood donors with people seeking blood through blood group and location-based searching. Our aim is to reduce the time and difficulty involved in finding a suitable donor during a blood requirement.
            </p>
          </div>

          {/* Important Medical Disclaimer Box */}
          <div id="important-note" className="p-6 md:p-8 bg-amber-50/80 rounded-3xl border border-amber-200 space-y-4 shadow-xs">
            <div className="flex items-center gap-3 text-amber-900 font-black text-lg">
              <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
              <span>Important Medical Disclaimer</span>
            </div>
            <p className="text-sm md:text-base text-amber-900 leading-relaxed font-medium">
              Blood Connect is only a platform that connects blood donors with people seeking blood. We do not collect, store, test, or handle blood in any way. All medical checks, compatibility, donor eligibility, and the donation process must be verified and handled by the respective hospital or doctor.
            </p>

            <div className="pt-4 border-t border-amber-200/80">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={hasAcknowledgedDisclaimer}
                  onChange={(e) => setHasAcknowledgedDisclaimer(e.target.checked)}
                  className="w-5 h-5 rounded border-amber-300 text-red-600 focus:ring-red-500 accent-red-600 cursor-pointer"
                />
                <span className="text-sm font-bold text-slate-900 group-hover:text-red-600 transition-colors">
                  I have read and understood the above information.
                </span>
              </label>
            </div>
          </div>
        </div>
      </section>

      {/* ================= PLATFORM STATISTICS ================= */}
      <section className="py-12 bg-slate-50 border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="w-10 h-10 bg-red-100 rounded-xl text-red-600 flex items-center justify-center mx-auto mb-3">
                <Heart className="w-5 h-5 fill-red-600" />
              </div>
              <div className="text-3xl font-black text-slate-900">{stats.total_donors}+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Voluntary Donors
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl text-emerald-600 flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div className="text-3xl font-black text-slate-900">{stats.available_donors}</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Available Right Now
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="w-10 h-10 bg-blue-100 rounded-xl text-blue-600 flex items-center justify-center mx-auto mb-3">
                <MapPin className="w-5 h-5" />
              </div>
              <div className="text-3xl font-black text-slate-900">11+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Regions Covered
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="w-10 h-10 bg-amber-100 rounded-xl text-amber-600 flex items-center justify-center mx-auto mb-3">
                <Clock className="w-5 h-5" />
              </div>
              <div className="text-3xl font-black text-slate-900">&lt; 15m</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Avg. Connection Speed
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= HOW BLOOD CONNECT WORKS ================= */}
      <section id="how-it-works" className="py-16 md:py-24 bg-white border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-bold uppercase tracking-widest text-red-600">
              Simple & Transparent
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900">
              How Blood Connect Works
            </h2>
            <p className="text-sm text-slate-600">
              A privacy-focused 3-step workflow designed to connect donors and patients in minutes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="bg-slate-50 rounded-3xl p-8 border border-slate-200 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                1
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Search by Blood Group & Location</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                Filter donors by required blood group and any preferred location in Tamil Nadu. Privacy is strictly safeguarded: donor contact numbers remain concealed during public search.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <Shield className="w-4 h-4 text-emerald-600" />
                <span>Zero phone number harvesting</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-50 rounded-3xl p-8 border border-slate-200 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                2
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Send Blood Request</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                Submit an urgent request specifying the hospital name, patient details, urgency level, and units required. The donor receives an instant notification.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <Activity className="w-4 h-4 text-rose-600" />
                <span>Real-time In-app & SMS alert</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-50 rounded-3xl p-8 border border-slate-200 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                3
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Donor Accepts & Connects</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                When the donor clicks Accept, both parties receive each other's contact number for direct phone calls and WhatsApp coordination at the hospital.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <PhoneCall className="w-4 h-4 text-emerald-600" />
                <span>Direct Contact Unlocked</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= DONOR ELIGIBILITY CHECKLIST ================= */}
      <section id="eligibility" className="py-16 md:py-20 bg-slate-50 border-t border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <span className="text-xs font-bold uppercase tracking-widest text-red-600">
                Safety & Compliance
              </span>
              <h2 className="text-3xl sm:text-4xl font-black text-slate-900">
                Who Can Donate Blood?
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Before registering as a voluntary donor, please ensure you satisfy standard national blood donation criteria.
              </p>

              <div className="space-y-3.5">
                {[
                  'Age between 18 and 65 years old',
                  'Body weight must be at least 45 kg (100 lbs)',
                  'Minimum 90 days gap since your last whole blood donation',
                  'Hemoglobin level must be at least 12.5 g/dL',
                  'Free from active infections, flu, cold, or fever in the past 48 hours',
                  'No major surgery or tattoo in the past 6 to 12 months',
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-sm text-slate-800 font-medium">
                    <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="pt-2">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-6 py-3.5 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-md shadow-red-500/20 transition-all cursor-pointer"
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Register as Eligible Donor</span>
                </Link>
              </div>
            </div>

            {/* Right Card: Fact Box */}
            <div className="bg-gradient-to-br from-red-600 to-rose-700 rounded-3xl p-8 text-white shadow-xl">
              <Droplet className="w-12 h-12 fill-white/20 text-white mb-6" />
              <h3 className="text-2xl font-bold mb-3">1 Donation = Up to 3 Lives Saved</h3>
              <p className="text-sm text-rose-100 leading-relaxed mb-6">
                Your single unit of donated blood can be separated into red blood cells, plasma, and platelets to help multiple patients undergoing emergency surgeries, trauma care, and cancer treatments.
              </p>
              <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-xs border border-white/20 space-y-2">
                <div className="text-xs font-semibold text-rose-200 uppercase tracking-wider">
                  Important Reminder
                </div>
                <p className="text-xs text-white leading-relaxed">
                  Hospital blood banks conduct complete pre-donation cross-matching and infectious disease tests before every transfusion.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
