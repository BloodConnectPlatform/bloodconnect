'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { PhoneCall, ShieldCheck, AlertCircle, AlertTriangle } from 'lucide-react';
import { openPlatformNotice } from '@/components/common/PlatformNoticeModal';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {/* Col 1: Brand & Purpose */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/10 p-1.5 flex items-center justify-center border border-white/15 shadow-md">
                <Image
                  src="/logo-icon.png"
                  alt="Blood Connect Logo"
                  width={34}
                  height={34}
                  className="object-contain"
                />
              </div>
              <div>
                <span className="text-xl font-black text-white tracking-tight flex items-center gap-1">
                  Blood<span className="text-red-500">Connect</span>
                </span>
                <span className="block text-[10px] font-medium text-slate-400 -mt-0.5 tracking-wide">
                  Connecting Donors. Reaching Those in Need.
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              A community-driven, voluntary blood donor discovery platform connecting life-saving donors with people in urgent need across Coimbatore.
            </p>
            <div className="pt-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Non-Profit & Privacy-First</span>
              </div>
            </div>
          </div>

          {/* Col 2: Emergency Helplines */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
              Emergency Numbers
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">Ambulance / Emergency</span>
                <span className="text-red-400 font-bold flex items-center gap-1">
                  <PhoneCall className="w-3.5 h-3.5" /> 108
                </span>
              </li>
              <li className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">TN Health Helpline</span>
                <span className="text-red-400 font-bold flex items-center gap-1">
                  <PhoneCall className="w-3.5 h-3.5" /> 104
                </span>
              </li>
              <li className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-lg border border-slate-800">
                <span className="text-slate-300 font-medium">National Blood Helpline</span>
                <span className="text-red-400 font-bold flex items-center gap-1">
                  <PhoneCall className="w-3.5 h-3.5" /> 1910
                </span>
              </li>
            </ul>
          </div>

          {/* Col 3: Quick Navigation */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
              Quick Links
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/find-donor" className="hover:text-red-400 transition-colors">
                  Find a Donor
                </Link>
              </li>
              <li>
                <Link href="/register" className="hover:text-red-400 transition-colors">
                  Register as Donor
                </Link>
              </li>
              <li>
                <Link href="/#about-initiative" className="hover:text-red-400 transition-colors">
                  About Our Initiative
                </Link>
              </li>
              <li>
                <Link href="/#how-it-works" className="hover:text-red-400 transition-colors">
                  How It Works
                </Link>
              </li>
              <li>
                <button
                  type="button"
                  onClick={openPlatformNotice}
                  className="hover:text-amber-400 text-amber-300/90 transition-colors text-left cursor-pointer flex items-center gap-1"
                >
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  <span>Platform Notice & Disclaimer</span>
                </button>
              </li>
              <li>
                <Link href="/privacy-policy" className="hover:text-red-400 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-red-400 transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Regions Covered */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
              Covered Locations
            </h4>
            <p className="text-xs text-slate-400">
              Active in Coimbatore, Sulur, Tiruppur, Pollachi, Mettupalayam, Avinashi, Palladam, Udumalpet, Annur, Madukkarai, Perur.
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {['Coimbatore', 'Tiruppur', 'Pollachi', 'Sulur'].map((loc) => (
                <span
                  key={loc}
                  className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-400 border border-slate-700/60"
                >
                  {loc}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Mandatory Non-Blood-Bank Banner with click-to-view alert */}
        <div
          onClick={openPlatformNotice}
          className="p-4 bg-slate-800/80 hover:bg-slate-800 rounded-2xl border border-slate-700/80 mb-8 cursor-pointer transition-colors"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 leading-relaxed">
              <strong className="text-white">Legal & Medical Notice:</strong> Blood Connect is strictly a communication network connecting voluntary donors with requesters. Blood Connect is <strong>NOT a blood bank</strong> and does not collect, test, transport, process, or deliver blood. (Click to read full notice)
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} Blood Connect — Connecting Donors. Reaching Those in Need.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy-policy" className="hover:text-slate-300 transition-colors">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-slate-300 transition-colors">
              Terms of Service
            </Link>
            <span>•</span>
            <span>Emergency Use Only</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
