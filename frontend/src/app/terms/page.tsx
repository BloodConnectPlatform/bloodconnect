'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileText,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Ban,
  ArrowLeft,
  Scale,
  Hospital,
} from 'lucide-react';
import { api } from '@/lib/api';
import { LegalDocument } from '@/types';

const FALLBACK_TERMS_DOC: LegalDocument = {
  title: 'Terms of Service',
  last_updated: 'September 2026',
  platform_name: 'BloodConnect',
  summary:
    'BloodConnect is a non-profit, community-driven emergency communication intermediary connecting voluntary blood donors with patients across Coimbatore. BloodConnect is NOT a blood bank and does not collect, test, process, or deliver blood. All medical verifications and donations must take place at licensed hospitals. Any commercial buying, selling, or charging of fees for blood is strictly illegal and prohibited.',
  sections: [
    {
      title: '1. Acceptance of Terms',
      content:
        'By accessing, registering, or using the BloodConnect platform (the "Platform"), you acknowledge that you have read, understood, and agreed to be bound by these Terms of Service. If you do not agree with any part of these terms, you must discontinue use of the platform immediately.',
    },
    {
      title: '2. Nature of Platform: Emergency Intermediary Communication Tool Only',
      content:
        'BloodConnect is strictly a voluntary intermediary communication directory designed to connect voluntary blood donors with individuals in urgent medical need.',
      points: [
        'NOT A BLOOD BANK: BloodConnect is NOT a blood bank, hospital, clinical laboratory, or medical establishment.',
        'No Blood Handling: BloodConnect does not collect, draw, screen, test, cross-match, process, store, transport, or administer blood or blood components.',
        'Communication Facilitation Only: The platform\'s sole function is to facilitate direct communication between willing voluntary donors and blood requesters during emergencies.',
      ],
    },
    {
      title: '3. Mandatory Hospital Clinical Screening & Medical Disclaimer',
      content:
        'All medical procedures, eligibility evaluations, and blood transfusions must be conducted strictly at authorized hospitals or licensed clinical blood banks.',
      points: [
        'No Medical Advice: BloodConnect does not provide medical diagnoses, treatment advice, or medical clearance of donors.',
        'Mandatory Clinical Verification: Hospitals and certified blood banks are solely responsible for conducting required medical donor screenings, infectious disease testing (e.g., HIV, Hepatitis B/C, Malaria, Syphilis), hemoglobin testing, blood group confirmation, and cross-matching.',
        'Clinical Discretion: The hospital or attending medical officer has full discretion to determine donor eligibility in accordance with National Blood Transfusion Council (NBTC) guidelines.',
      ],
    },
    {
      title: '4. Strictly Voluntary & Non-Commercial: Absolute Ban on Sale of Blood',
      content:
        'Blood donation facilitated through BloodConnect is strictly voluntary, altruistic, and unpaid.',
      points: [
        'No Monetary Exchange: Buying, selling, demanding remuneration, offering cash, or charging any fees for blood donation is strictly illegal under the Drugs and Cosmetics Act, 1940 and Indian Penal laws.',
        'Zero-Tolerance Policy: Any user attempting to buy, sell, or solicit money or goods for blood donation will face immediate permanent account termination, blacklisting, and reporting to legal law enforcement authorities.',
      ],
    },
    {
      title: '5. Donor Eligibility & Account Responsibilities',
      content:
        'To maintain platform safety and medical integrity, donors and requesters agree to strict eligibility and conduct standards.',
      points: [
        'Age Limit: Voluntary donors must be between 18 and 65 years of age.',
        'Truthful Information: Users must provide accurate, current, and genuine details including their real name, actual blood group, and active mobile number.',
        'No Impersonation: Creating fake profiles, posting bogus emergency requests, or impersonating medical personnel is strictly prohibited.',
        'Contact Respect: Contact details obtained upon request acceptance must be used solely for coordinating the specific blood donation request. Harassment, verbal abuse, spam, or unsolicited outreach is strictly prohibited.',
      ],
    },
    {
      title: '6. Limitation of Liability',
      content:
        'BloodConnect is provided on an "AS IS" and "AS AVAILABLE" basis to support the community in good faith during medical emergencies.',
      points: [
        'No Guarantee of Availability: BloodConnect does not guarantee that a registered donor will be available, will respond, will arrive at the hospital, or will be deemed medically eligible by hospital staff.',
        'No Liability for Transfusion Outcomes: BloodConnect and its maintainers assume no responsibility or liability for medical complications, adverse transfusion reactions, hospital delays, or disputes between donors and requesters.',
        'Platform Availability: We strive to maintain continuous platform availability but do not guarantee uninterrupted or error-free operation during network or technical disruptions.',
      ],
    },
    {
      title: '7. Platform Moderation, Auditing & Account Termination',
      content:
        'Platform administrators reserve the right to review reported profiles, monitor emergency requests, deactivate inactive or offending accounts, and cooperate with law enforcement authorities in cases of platform misuse, fraud, or violations of applicable laws.',
    },
    {
      title: '8. Changes to Terms',
      content:
        'We may update these Terms of Service periodically to reflect platform enhancements or regulatory requirements. Continued use of BloodConnect after updates constitute acceptance of the revised terms.',
    },
  ],
};

export default function TermsOfServicePage() {
  const [doc, setDoc] = useState<LegalDocument>(FALLBACK_TERMS_DOC);

  useEffect(() => {
    api
      .getTerms()
      .then((data) => {
        if (data && data.sections && data.sections.length > 0) {
          setDoc(data);
        }
      })
      .catch(() => {
        // Fallback remains active seamlessly
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-red-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
          <span className="text-xs font-semibold px-3 py-1 bg-amber-100 text-amber-800 rounded-full">
            Effective: {doc.last_updated}
          </span>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-4">
          <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-2xl flex items-center justify-center mb-2">
            <Scale className="w-6 h-6" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            {doc.title}
          </h1>
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
            {doc.summary}
          </p>

          {/* Key Legal Highlights Card */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100 mt-6">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <Hospital className="w-5 h-5 text-red-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">NOT a Blood Bank</h4>
              <p className="text-xs text-slate-500 mt-1">Hospital clinical verification mandatory.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <Ban className="w-5 h-5 text-rose-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Strictly Non-Profit</h4>
              <p className="text-xs text-slate-500 mt-1">Buying or selling blood is strictly illegal.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <ShieldCheck className="w-5 h-5 text-emerald-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Emergency Protocol</h4>
              <p className="text-xs text-slate-500 mt-1">Voluntary donor discovery for emergency need.</p>
            </div>
          </div>
        </div>

        {/* Sections Content */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-8">
          {doc.sections.map((section, idx) => (
            <div key={idx} className="space-y-3 pb-6 border-b border-slate-100 last:border-0 last:pb-0">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <span>{section.title}</span>
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                {section.content}
              </p>
              {section.points && section.points.length > 0 && (
                <ul className="space-y-2 pt-1 pl-2">
                  {section.points.map((pt, pIdx) => (
                    <li key={pIdx} className="text-xs sm:text-sm text-slate-600 flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>

        {/* Footer Navigation */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} {doc.platform_name} — Emergency Intermediary Communication Tool.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy-policy" className="hover:text-red-600 font-semibold transition-colors">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link href="/" className="hover:text-red-600 font-semibold transition-colors">
              Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
