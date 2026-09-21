'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, CheckCircle2, X } from 'lucide-react';

export function openPlatformNotice() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('open-platform-notice'));
  }
}

export const PlatformNoticeModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Show alert automatically on opening the platform if not acknowledged in this session
    const acknowledged = sessionStorage.getItem('bloodconnect_notice_acknowledged');
    if (!acknowledged) {
      // Short delay for smooth entrance
      const timer = setTimeout(() => {
        setIsOpen(true);
      }, 400);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener('open-platform-notice', handleOpen);
    return () => window.removeEventListener('open-platform-notice', handleOpen);
  }, []);

  const handleAcknowledge = () => {
    sessionStorage.setItem('bloodconnect_notice_acknowledged', 'true');
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header with Amber Warning Accent */}
        <div className="bg-gradient-to-r from-amber-600 via-rose-600 to-red-600 p-6 text-white relative">
          <button
            onClick={handleAcknowledge}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-1.5 rounded-full hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Close Notice"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center flex-shrink-0 backdrop-blur-xs">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-[11px] font-black uppercase tracking-wider text-amber-200">
                Important Medical Notice
              </span>
              <h2 className="text-xl font-black text-white leading-tight">
                Platform Notice & Disclaimer
              </h2>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 text-slate-700">
          <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-950 font-semibold leading-relaxed">
            Blood Connect is an emergency intermediary communication platform connecting voluntary donors with patients across Coimbatore.
          </div>

          <div className="space-y-3 text-xs leading-relaxed">
            <div className="flex items-start gap-3">
              <div className="p-1.5 bg-red-100 text-red-600 rounded-lg mt-0.5 flex-shrink-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <strong className="text-slate-900 font-bold block mb-0.5">NOT a Blood Bank</strong>
                <span>
                  We do <strong>not</strong> collect, store, test, process, or deliver blood. We only assist in discovering willing voluntary donors.
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-1.5 bg-emerald-100 text-emerald-600 rounded-lg mt-0.5 flex-shrink-0">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <strong className="text-slate-900 font-bold block mb-0.5">Hospital Clinical Verification Required</strong>
                <span>
                  All donor eligibility checks, compatibility testing, cross-matching, and transfusion procedures must be strictly verified and performed by authorized hospital doctors and certified blood banks.
                </span>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={handleAcknowledge}
              className="w-full py-3.5 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-black text-sm rounded-2xl shadow-lg shadow-red-600/20 hover:shadow-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>I Understand & Proceed</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
