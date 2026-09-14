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
  PhoneCall,
  Activity,
  Users,
} from 'lucide-react';
import { BloodGroup, LocationItem } from '@/types';
import { api } from '@/lib/api';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function HomePage() {
  const router = useRouter();
  const [locations, setLocations] = useState<LocationItem[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<BloodGroup | ''>('');
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [stats, setStats] = useState({
    total_donors: 148,
    available_donors: 112,
    total_locations: 11,
    avg_response_mins: 15,
  });

  useEffect(() => {
    api.getLocations().then((data) => {
      setLocations(data);
    }).catch(() => {
      // Fallback default TN locations
      setLocations([
        { id: 1, district: 'Coimbatore', taluk: 'Coimbatore South', is_active: true },
        { id: 2, district: 'Coimbatore', taluk: 'Coimbatore North', is_active: true },
        { id: 3, district: 'Coimbatore', taluk: 'Sulur', is_active: true },
        { id: 4, district: 'Coimbatore', taluk: 'Pollachi', is_active: true },
        { id: 5, district: 'Coimbatore', taluk: 'Mettupalayam', is_active: true },
        { id: 6, district: 'Tiruppur', taluk: 'Tiruppur North', is_active: true },
        { id: 7, district: 'Tiruppur', taluk: 'Avinashi', is_active: true },
        { id: 8, district: 'Tiruppur', taluk: 'Palladam', is_active: true },
        { id: 9, district: 'Tiruppur', taluk: 'Udumalpet', is_active: true },
      ]);
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

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = new URLSearchParams();
    if (selectedGroup) query.append('blood_group', selectedGroup);
    if (selectedLocation) query.append('location_id', selectedLocation);
    router.push(`/find-donor?${query.toString()}`);
  };

  return (
    <div className="flex flex-col min-h-full">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-red-50/70 via-white to-slate-50 pt-12 pb-20 md:pt-20 md:pb-28 border-b border-slate-200/60">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            {/* Status Pill */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-100 text-red-800 text-xs font-semibold shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
              <span>Voluntary Donor Network • Tamil Nadu</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15]">
              Connecting Blood Donors with{' '}
              <span className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 bg-clip-text text-transparent">
                Lives in Need
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
              Blood Connect connects voluntary blood donors with families and patients in urgent medical emergencies across Coimbatore, Tiruppur, and surrounding regions.
            </p>

            {/* Dual Primary Call-to-Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                href="/find-donor"
                className="w-full sm:w-auto px-8 py-4 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold text-base rounded-2xl shadow-lg shadow-red-600/25 hover:shadow-xl hover:shadow-red-600/30 transition-all flex items-center justify-center gap-3 group cursor-pointer"
              >
                <Search className="w-5 h-5 text-red-100 group-hover:scale-110 transition-transform" />
                <span>NEED BLOOD? FIND A DONOR</span>
                <ArrowRight className="w-4 h-4 text-red-200 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link
                href="/register"
                className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-800 hover:text-red-600 font-bold text-base rounded-2xl border-2 border-slate-200 hover:border-red-200 shadow-sm transition-all flex items-center justify-center gap-3 cursor-pointer"
              >
                <Heart className="w-5 h-5 text-red-500 fill-red-500" />
                <span>WANT TO DONATE? REGISTER</span>
              </Link>
            </div>
          </div>

          {/* Quick Search Card Widget */}
          <div className="mt-14 max-w-4xl mx-auto bg-white rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-200/50 border border-slate-200/80">
            <div className="flex items-center gap-2 mb-4 text-slate-800 font-bold text-base md:text-lg">
              <div className="p-2 bg-red-50 rounded-xl text-red-600">
                <Search className="w-5 h-5" />
              </div>
              <span>Quick Donor Discovery</span>
            </div>

            <form onSubmit={handleQuickSearch} className="space-y-6">
              {/* Blood Group Chips */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  1. Select Blood Group Needed
                </label>
                <div className="grid grid-cols-4 sm:grid-cols-8 gap-2.5">
                  {BLOOD_GROUPS.map((bg) => (
                    <button
                      key={bg}
                      type="button"
                      onClick={() => setSelectedGroup(selectedGroup === bg ? '' : bg)}
                      className={`py-3 px-2 rounded-xl font-bold text-sm transition-all border text-center cursor-pointer ${
                        selectedGroup === bg
                          ? 'bg-red-600 text-white border-red-600 shadow-md shadow-red-500/30 scale-105'
                          : 'bg-slate-50 hover:bg-red-50 text-slate-800 border-slate-200 hover:border-red-200'
                      }`}
                    >
                      {bg}
                    </button>
                  ))}
                </div>
              </div>

              {/* Location and Search Button */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    2. Choose Preferred Location / District
                  </label>
                  <div className="relative">
                    <MapPin className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <select
                      value={selectedLocation}
                      onChange={(e) => setSelectedLocation(e.target.value)}
                      className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all cursor-pointer"
                    >
                      <option value="">All Locations (Coimbatore, Tiruppur & nearby)</option>
                      {locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.taluk} ({loc.district})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full py-3 px-6 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-md shadow-red-500/20 hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer h-[46px]"
                  >
                    <Search className="w-4 h-4" />
                    Find Matching Donors
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Mandatory Medical Disclaimer Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 z-10">
        <MedicalDisclaimer variant="card" />
      </div>

      {/* Platform Statistics */}
      <section className="py-12 bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 bg-red-100 rounded-xl text-red-600 flex items-center justify-center mx-auto mb-3">
                <Heart className="w-5 h-5 fill-red-600" />
              </div>
              <div className="text-3xl font-black text-slate-900">{stats.total_donors}+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Voluntary Donors
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl text-emerald-600 flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div className="text-3xl font-black text-slate-900">{stats.available_donors}</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                Available Right Now
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 bg-blue-100 rounded-xl text-blue-600 flex items-center justify-center mx-auto mb-3">
                <MapPin className="w-5 h-5" />
              </div>
              <div className="text-3xl font-black text-slate-900">11</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wider">
                TN Taluks Covered
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100">
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

      {/* How Blood Connect Works */}
      <section id="how-it-works" className="py-16 md:py-24 bg-slate-50">
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
            <div className="bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                1
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Search by Blood Group</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                Filter donors by required blood group and closest taluk in Tamil Nadu. Privacy is safeguarded: donor contact numbers remain concealed during public search.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <Shield className="w-4 h-4 text-emerald-600" />
                <span>Zero phone number harvesting</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                2
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Send Blood Request</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                Submit an urgent request specifying the hospital name, patient details, urgency level, and units required. The donor receives an instant notification.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <Activity className="w-4 h-4 text-rose-600" />
                <span>Real-time SMS & In-app alert</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xs relative flex flex-col">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center font-black text-xl mb-6">
                3
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Donor Accepts & Connects</h3>
              <p className="text-sm text-slate-600 leading-relaxed flex-1">
                When the donor clicks Accept, both parties receive each other's contact number for direct phone calls and WhatsApp coordination at the hospital.
              </p>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs font-semibold text-slate-500">
                <PhoneCall className="w-4 h-4 text-emerald-600" />
                <span>Direct Contact Unlocked</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Donor Eligibility Checklist */}
      <section id="eligibility" className="py-16 md:py-20 bg-white border-t border-slate-200/60">
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
