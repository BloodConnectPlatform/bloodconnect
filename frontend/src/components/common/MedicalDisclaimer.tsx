import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

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
      <div className={`flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 ${className}`}>
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <p>
          <strong>Notice:</strong> Blood Connect connects willing donors. Donor eligibility, blood compatibility, and medical testing must be strictly verified at a certified hospital or blood bank.
        </p>
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div className={`bg-gradient-to-r from-amber-500/10 via-red-500/10 to-amber-500/10 border-y border-amber-200 py-3 px-4 ${className}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 text-xs md:text-sm text-amber-900 font-medium">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span>
              <strong>Platform Notice:</strong> Blood Connect is a voluntary donor connection platform and <strong>NOT a blood bank</strong>. We do not store, transport, or clinically test blood.
            </span>
          </div>
          <span className="hidden lg:inline text-xs text-amber-700 font-normal">
            Always verify compatibility through certified medical practitioners.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-amber-50/80 border border-amber-200/90 rounded-xl p-4 md:p-5 shadow-xs ${className}`}>
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-100 rounded-lg text-amber-700 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-amber-900">
            Important Medical & Safety Disclaimer
          </h4>
          <p className="text-xs md:text-sm text-amber-800 leading-relaxed">
            Blood Connect is an intermediary communication tool to discover voluntary blood donors.
            <strong> Blood Connect does not collect, test, store, or deliver blood. </strong>
            All medical compatibility tests, infectious disease screenings, donor hemoglobin checks, and transfusion procedures must be performed by licensed medical professionals at authorized healthcare facilities.
          </p>
        </div>
      </div>
    </div>
  );
};
