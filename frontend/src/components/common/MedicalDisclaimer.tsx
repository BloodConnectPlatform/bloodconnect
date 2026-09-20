'use client';

import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { openPlatformNotice } from './PlatformNoticeModal';

interface MedicalDisclaimerProps {
  variant?: 'banner' | 'card' | 'compact';
  className?: string;
}

export const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({
  variant = 'card',
  className = '',
}) => {
  if (variant === 'compact') {
    return (
      <div
        onClick={openPlatformNotice}
        className={`flex items-center gap-2 p-3 bg-amber-50 hover:bg-amber-100/70 border border-amber-200 rounded-xl text-xs text-amber-900 cursor-pointer transition-colors ${className}`}
        title="Click to view full platform notice"
      >
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <p>
          <strong>Notice:</strong> Blood Connect is <strong>not a blood bank</strong>. Donor eligibility, blood compatibility, and medical testing must be strictly verified at a certified hospital.
        </p>
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div className={`bg-gradient-to-r from-amber-500/10 via-red-500/10 to-amber-500/10 border-y border-amber-200 py-2.5 px-4 ${className}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 text-xs text-amber-950 font-medium">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span>
              <strong>Platform Notice:</strong> Blood Connect is an intermediary discovery tool and <strong>NOT a blood bank</strong>.
            </span>
          </div>
          <button
            type="button"
            onClick={openPlatformNotice}
            className="text-xs text-red-600 font-bold hover:underline cursor-pointer"
          >
            View Details
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={openPlatformNotice}
      className={`bg-amber-50/90 hover:bg-amber-50 border border-amber-200/90 rounded-2xl p-4 md:p-5 shadow-2xs cursor-pointer transition-colors ${className}`}
      title="Click to view full platform notice"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-100 rounded-xl text-amber-700 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-amber-950">
              Important Medical & Safety Disclaimer
            </h4>
            <span className="text-[11px] font-bold text-amber-700 underline">
              View Notice
            </span>
          </div>
          <p className="text-xs md:text-sm text-amber-900 leading-relaxed font-medium">
            Blood Connect is an intermediary communication tool to discover voluntary blood donors.
            <strong> Blood Connect does not collect, test, store, or deliver blood. </strong>
            All medical compatibility tests, infectious disease screenings, donor hemoglobin checks, and transfusion procedures must be performed by licensed medical professionals at authorized healthcare facilities.
          </p>
        </div>
      </div>
    </div>
  );
};
