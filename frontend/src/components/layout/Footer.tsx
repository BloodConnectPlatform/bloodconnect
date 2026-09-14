import React from 'react';
import Link from 'next/link';
import { Droplet, PhoneCall, ShieldCheck, HeartHandshake, AlertCircle } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {/* Col 1: Brand & Purpose */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-red-600 flex items-center justify-center text-white shadow-md shadow-red-500/20">
                <Droplet className="w-5 h-5 fill-white" />
              </div>
              <span className="text-xl font-bold text-white tracking-tight">
                Blood<span className="text-red-500">Connect</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              A community-driven, voluntary blood donor discovery platform connecting life-saving donors with people in urgent need across Tamil Nadu.
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
                  Find Blood Donors
                </Link>
              </li>
              <li>
                <Link href="/register" className="hover:text-red-400 transition-colors">
                  Become a Voluntary Donor
                </Link>
              </li>
              <li>
                <Link href="/#how-it-works" className="hover:text-red-400 transition-colors">
                  How the Platform Works
                </Link>
              </li>
              <li>
                <Link href="/#eligibility" className="hover:text-red-400 transition-colors">
                  Donor Eligibility Guidelines
                </Link>
              </li>
              <li>
                <Link href="/admin" className="text-slate-500 hover:text-slate-400 transition-colors">
                  Admin Portal
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

        {/* Mandatory Non-Blood-Bank Banner */}
        <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700/80 mb-8">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 leading-relaxed">
              <strong className="text-white">Legal & Medical Notice:</strong> Blood Connect is strictly a communication network connecting voluntary donors with requesters. Blood Connect is <strong>NOT a blood bank</strong> and does not collect, test, transport, process, or deliver blood. All compatibility checks, grouping tests, and clinical medical screenings must be conducted by licensed healthcare professionals at authorized hospitals or blood banks.
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} Blood Connect. Built for life-saving community support in Tamil Nadu.</p>
          <div className="flex items-center gap-4">
            <span>Voluntary & Free Platform</span>
            <span>•</span>
            <span>Emergency Use Only</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
