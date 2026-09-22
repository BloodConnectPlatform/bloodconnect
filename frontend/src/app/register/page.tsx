'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import {
  Heart,
  Droplet,
  Phone,
  KeyRound,
  User,
  MapPin,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  ArrowRight,
  ArrowLeft,
  MessageCircle,
} from 'lucide-react';
import { BloodGroup, Gender, LocationItem } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';
import { redirectToWhatsAppLogin } from '@/lib/whatsapp';
import { DEFAULT_LOCATIONS } from '@/lib/constants';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

function DonorRegistrationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();

  // Wizard Steps: 1: Phone, 2: OTP, 3: Profile Form, 4: Success
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form State
  const [mobileNumber, setMobileNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [verificationToken, setVerificationToken] = useState('');
  const [isPreverified, setIsPreverified] = useState(false);

  useEffect(() => {
    const mobileParam = searchParams.get('mobile');
    const tokenParam = searchParams.get('token');
    if (mobileParam) {
      setMobileNumber(mobileParam);
    }
    if (tokenParam) {
      setVerificationToken(tokenParam);
      setIsPreverified(true);
      setStep(3);
    }
  }, [searchParams]);

  const [fullName, setFullName] = useState('');
  const [bloodGroup, setBloodGroup] = useState<BloodGroup>('A+');
  const [gender, setGender] = useState<Gender>('MALE');
  const [dateOfBirth, setDateOfBirth] = useState('2000-01-01');
  const [locationId, setLocationId] = useState<number | ''>(DEFAULT_LOCATIONS[0].id);
  const [isAvailable, setIsAvailable] = useState(true);
  const [agreeDisclaimer, setAgreeDisclaimer] = useState(false);

  // Meta
  const [locations, setLocations] = useState<LocationItem[]>(DEFAULT_LOCATIONS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    api.getLocations().then((res) => {
      if (res && res.length > 0) {
        setLocations(res);
        setLocationId((prev) => {
          const exists = res.some((l) => l.id === prev);
          return exists ? prev : res[0].id;
        });
      }
    }).catch(() => {
      setLocations(DEFAULT_LOCATIONS);
      setLocationId(DEFAULT_LOCATIONS[0].id);
    });
  }, []);


  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldown]);

  const normalizePhone = (num: string) => {
    const cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return `+91${cleaned}`;
    if (cleaned.length === 12 && cleaned.startsWith('91')) return `+${cleaned}`;
    if (num.startsWith('+91') && cleaned.length === 12) return num;
    return `+91${cleaned}`;
  };

  // Step 1: Send OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const formatted = normalizePhone(mobileNumber);
    if (!/^\+91[6-9]\d{9}$/.test(formatted)) {
      setError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.sendOtp(formatted, 'DONOR_REGISTRATION');
      setStep(2);
      setCooldown(res.cooldown_seconds || 60);
      if (res.debug_otp) {
        setOtpCode(res.debug_otp);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (otpCode.trim().length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setIsLoading(true);
    try {
      const formatted = normalizePhone(mobileNumber);
      const res = await api.verifyOtp(formatted, otpCode.trim());
      if (res.verification_token) {
        setVerificationToken(res.verification_token);
      }
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Complete Profile
  const handleCompleteProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }

    // Validate Age >= 18
    const dob = new Date(dateOfBirth);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
      age--;
    }

    if (age < 18) {
      setError('You must be at least 18 years of age to register as a voluntary blood donor.');
      return;
    }

    if (age > 65) {
      setError('Blood donors must be between 18 and 65 years of age.');
      return;
    }

    if (!locationId) {
      setError('Please select your location / area.');
      return;
    }

    if (!agreeDisclaimer) {
      setError('Please acknowledge the voluntary blood donation safety and medical disclaimer.');
      return;
    }

    setIsLoading(true);
    try {
      const formatted = normalizePhone(mobileNumber);
      await api.registerDonor({
        mobile_number: formatted,
        verification_token: verificationToken,
        full_name: fullName.trim(),
        blood_group: bloodGroup,
        gender,
        date_of_birth: dateOfBirth,
        location_id: Number(locationId),
        is_available: isAvailable,
      });

      await refreshUser();
      setStep(4);
    } catch (err: any) {
      setError(err.message || 'Failed to complete registration.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 bg-slate-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        {/* Wizard Card */}
        <div className="bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 p-6 md:p-8 text-white relative">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center text-white backdrop-blur-xs p-1 border border-white/20 shadow-xs">
                <Image
                  src="/logo-icon.png"
                  alt="Blood Connect"
                  width={32}
                  height={32}
                  className="object-contain"
                />
              </div>
              <span className="text-xs font-bold uppercase tracking-widest text-rose-200">
                Join the Network
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black">Register as Voluntary Blood Donor</h1>
            <p className="text-xs sm:text-sm text-rose-100 mt-1">
              Your donation can save someone's life in an emergency. Free, secure, and privacy-protected.
            </p>

            {/* Step Indicator Bar */}
            <div className="flex items-center gap-2 mt-6">
              {[
                { num: 1, label: 'Mobile' },
                { num: 2, label: 'OTP' },
                { num: 3, label: 'Profile' },
              ].map((s) => (
                <div key={s.num} className="flex-1">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      step >= s.num ? 'bg-white' : 'bg-white/30'
                    }`}
                  />
                  <span className="block text-[10px] font-bold mt-1 text-rose-100 uppercase tracking-wider">
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Body */}
          <div className="p-6 md:p-8">
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3 text-xs text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* STEP 1: REGISTRATION METHOD SELECTION */}
            {step === 1 && (
              <div className="space-y-6">
                {/* Primary WhatsApp Registration Card */}
                <div className="p-6 bg-emerald-50/90 border-2 border-emerald-300 rounded-3xl space-y-4 shadow-xs">
                  <div className="flex items-center justify-between">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-black uppercase tracking-wider">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>Instant 1-Click Verification</span>
                    </div>
                    <span className="text-[11px] font-bold text-emerald-700 bg-white px-2 py-0.5 rounded-full border border-emerald-200">
                      Active
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-black text-emerald-950 flex items-center gap-2">
                      <MessageCircle className="w-5 h-5 text-emerald-600" />
                      <span>Register via WhatsApp</span>
                    </h3>
                    <p className="text-xs text-emerald-800 leading-relaxed mt-1.5">
                      Fastest and most reliable registration! Tap the button below to send <span className="font-mono font-bold bg-white px-1.5 py-0.5 rounded border border-emerald-300 text-emerald-900">REGISTER</span> to our official WhatsApp account. You will immediately receive a 1-click link to complete your donor profile in 30 seconds without waiting for SMS OTPs.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => redirectToWhatsAppLogin('REGISTER')}
                    className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-black text-sm rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2.5 cursor-pointer"
                  >
                    <MessageCircle className="w-5 h-5" />
                    <span>Open WhatsApp &amp; Send REGISTER</span>
                  </button>

                  <div className="pt-2 border-t border-emerald-200/60 flex items-center justify-between text-xs text-emerald-800">
                    <span>Already have a Blood Connect account?</span>
                    <button
                      type="button"
                      onClick={() => redirectToWhatsAppLogin('LOGIN')}
                      className="font-bold underline hover:text-emerald-950 cursor-pointer"
                    >
                      Sign In via WhatsApp
                    </button>
                  </div>
                </div>

                {/* SMS OTP Registration - Disabled & Marked Coming Soon */}
                <div className="pt-2">
                  <div className="relative flex items-center justify-center mb-4">
                    <div className="border-t border-slate-200 w-full" />
                    <div className="bg-white px-3 flex items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        SMS OTP Registration
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-100 text-amber-800 border border-amber-300">
                        Coming Soon
                      </span>
                    </div>
                    <div className="border-t border-slate-200 w-full" />
                  </div>

                  <div className="p-5 bg-slate-50/80 rounded-2xl border border-slate-200 space-y-4 opacity-60">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                        Mobile Number
                      </label>
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">
                          +91
                        </span>
                        <input
                          type="tel"
                          disabled
                          placeholder="9876543210"
                          value=""
                          className="w-full pl-14 pr-4 py-3 text-sm border border-slate-200 rounded-xl font-bold text-slate-500 bg-slate-100 cursor-not-allowed"
                        />
                      </div>
                    </div>

                    <button
                      type="button"
                      disabled
                      className="w-full py-3.5 bg-slate-200 text-slate-400 font-bold text-xs rounded-xl cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <span>SMS OTP Registration Unavailable (Coming Soon)</span>
                    </button>

                    <p className="text-[11px] text-slate-500 text-center leading-snug">
                      Direct SMS OTP registration is undergoing maintenance. Please tap the WhatsApp button above to register instantly.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: OTP VERIFICATION */}
            {step === 2 && (
              <form onSubmit={handleVerifyOtp} className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Enter 6-Digit OTP Code
                    </label>
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="text-xs font-bold text-red-600 hover:underline"
                    >
                      Change Number
                    </button>
                  </div>

                  <input
                    type="text"
                    maxLength={6}
                    placeholder="• • • • • •"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    required
                    autoFocus
                    className="w-full text-center tracking-[0.5em] text-2xl font-bold py-3.5 border border-slate-300 rounded-2xl font-mono text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                  />
                  <p className="text-xs text-slate-500 mt-2 text-center">
                    Enter the code sent to <strong>{mobileNumber}</strong>
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs">
                  {cooldown > 0 ? (
                    <span className="text-slate-400">Resend code in {cooldown}s</span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSendOtp}
                      className="text-red-600 font-bold hover:underline"
                    >
                      Resend OTP Code
                    </button>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="py-3.5 px-5 border border-slate-300 text-slate-700 font-bold text-sm rounded-2xl hover:bg-slate-50"
                  >
                    <ArrowLeft className="w-4 h-4" />
                  </button>

                  <button
                    type="submit"
                    disabled={isLoading || otpCode.length !== 6}
                    className="flex-1 py-3.5 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-bold text-sm rounded-2xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      <>
                        <span>Verify Phone</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* STEP 3: DONOR PROFILE DETAILS */}
            {step === 3 && (
              <form onSubmit={handleCompleteProfile} className="space-y-6">
                {isPreverified && (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-start gap-3 text-emerald-900">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <div className="font-bold text-emerald-950 text-sm">
                        WhatsApp Number Verified ({mobileNumber})
                      </div>
                      <p className="text-emerald-700 mt-0.5">
                        Your phone number was verified via WhatsApp. Complete your profile below to start saving lives!
                      </p>
                    </div>
                  </div>
                )}

                {/* Full Name */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Full Legal Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. S. Karthik"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-4 py-3 text-sm text-slate-900 bg-white border border-slate-300 rounded-xl font-medium placeholder:text-slate-400 focus:ring-2 focus:ring-red-500 outline-hidden"
                  />
                </div>

                {/* Blood Group & Gender */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Blood Group *
                    </label>
                    <select
                      value={bloodGroup}
                      onChange={(e) => setBloodGroup(e.target.value as BloodGroup)}
                      className="w-full px-4 py-3 text-sm font-bold text-slate-900 bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                    >
                      {BLOOD_GROUPS.map((bg) => (
                        <option key={bg} value={bg}>
                          {bg}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Gender *
                    </label>
                    <select
                      value={gender}
                      onChange={(e) => setGender(e.target.value as Gender)}
                      className="w-full px-4 py-3 text-sm font-medium text-slate-900 bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                    >
                      <option value="MALE">Male</option>
                      <option value="FEMALE">Female</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                </div>

                {/* Date of Birth & Location */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Date of Birth (Age &ge; 18) *
                    </label>
                    <input
                      type="date"
                      required
                      value={dateOfBirth}
                      onChange={(e) => setDateOfBirth(e.target.value)}
                      className="w-full px-4 py-3 text-sm font-medium text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Primary Location / Area *
                    </label>
                    <select
                      value={locationId}
                      onChange={(e) => setLocationId(Number(e.target.value))}
                      className="w-full px-4 py-3 text-sm font-medium text-slate-900 bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                    >
                      {locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Availability Switch */}
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="block text-xs font-bold text-slate-900">
                      Set Available for Requests Now
                    </span>
                    <span className="text-[11px] text-slate-500">
                      You can change this anytime from your Donor Hub.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={isAvailable}
                    onChange={(e) => setIsAvailable(e.target.checked)}
                    className="w-5 h-5 accent-red-600 rounded cursor-pointer"
                  />
                </div>

                {/* Mandatory Disclaimer Checkbox */}
                <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-2">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agreeDisclaimer}
                      onChange={(e) => setAgreeDisclaimer(e.target.checked)}
                      className="w-4 h-4 accent-red-600 rounded mt-0.5"
                    />
                    <span className="text-xs text-amber-900 leading-relaxed">
                      I confirm that I am donating voluntarily, meet the minimum age of 18, and understand that Blood Connect is <strong>not a blood bank</strong>. All medical and blood compatibility tests will be verified by certified hospital personnel.
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !fullName || !agreeDisclaimer}
                  className="w-full py-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-bold text-sm rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating Donor Profile...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Complete Donor Registration
                    </>
                  )}
                </button>
              </form>
            )}

            {/* STEP 4: REGISTRATION SUCCESSFUL (From PDF Spec Page 6) */}
            {step === 4 && (
              <div className="py-8 text-center space-y-6 animate-in fade-in">
                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-3xl flex items-center justify-center mx-auto shadow-md shadow-emerald-500/10">
                  <CheckCircle2 className="w-10 h-10" />
                </div>

                <div className="space-y-2">
                  <h2 className="text-2xl sm:text-3xl font-black text-slate-900">
                    Registration Successful!
                  </h2>
                  <p className="text-base text-red-600 font-semibold italic">
                    "Your willingness to help today could be someones hope tomorrow."
                  </p>
                </div>

                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs text-slate-600 leading-relaxed max-w-md mx-auto">
                  Your donor details have been securely recorded in the Blood Connect database. You will only be contacted when someone in your region urgently requires your blood group.
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => router.push('/donor/dashboard')}
                    className="w-full sm:w-auto px-8 py-4 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold text-sm rounded-2xl shadow-lg shadow-red-600/25 transition-all inline-flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>Proceed to Donor Hub</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Safety Banner */}
        <div className="mt-8">
          <MedicalDisclaimer variant="card" />
        </div>
      </div>
    </div>
  );
}

export default function DonorRegistrationPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        </div>
      }
    >
      <DonorRegistrationContent />
    </Suspense>
  );
}
