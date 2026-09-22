'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Trash2,
  ShieldAlert,
  CheckCircle2,
  ArrowLeft,
  FileText,
  UserX,
  PhoneCall,
  Clock,
  HelpCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import { LegalDocument } from '@/types';

const FALLBACK_DATA_DELETION_DOC: LegalDocument = {
  title: 'User Data Deletion Instructions',
  last_updated: 'September 2026',
  platform_name: 'BloodConnect',
  summary:
    'BloodConnect values your privacy and personal data rights. Users may request complete deletion or deactivation of their donor profile, account details, and personal information at any time. Follow the instructions below to submit a deletion request or manage your data.',
  sections: [
    {
      title: '1. Scope & Rights to Data Deletion',
      content:
        'In compliance with applicable privacy regulations and Meta Platform Policies, BloodConnect provides voluntary donors and requesters with the right to have their personal data completely erased from our active database. You may request data deletion at any time without incurring any penalty or cost.',
    },
    {
      title: '2. What Data Is Deleted Upon Request',
      content:
        'When a data deletion request is processed, the following information is permanently removed or scrubbed:',
      points: [
        'Donor Profile Information: Full name, 10-digit mobile number, blood group, date of birth, location, and contact consent records.',
        'User Account & Credentials: User identifier, mobile number associations, active session tokens, and authentication records.',
        'Notification Logs: Personal notification history and emergency request participant linkages.',
        'Database Removal: The personal account record is permanently expunged from active operational databases.',
      ],
    },
    {
      title: '3. Step-by-Step Instructions to Request Deletion',
      content:
        'Users can choose between temporary availability deactivation or permanent account erasure:',
      points: [
        'Option A (Instant Availability Pause): If you wish to stop appearing in public donor searches and stop receiving emergency blood requests immediately, log in to BloodConnect, navigate to your Donor Dashboard (/donor/dashboard), and toggle your availability status to "Unavailable".',
        'Option B (Permanent Account & Data Erasure): To permanently delete your entire profile and data, submit a data deletion request by emailing or contacting platform support with the subject "Data Deletion Request" and providing your registered 10-digit mobile number.',
        'Identity Verification: For security and to prevent fraudulent requests, a one-time verification code (OTP) will be sent to your registered phone number to confirm your identity before data deletion is executed.',
        'Confirmation: Upon successful OTP confirmation, your personal data will be purged from the platform.',
      ],
    },
    {
      title: '4. Processing Timeline',
      content:
        'Data deletion requests are reviewed and fulfilled within 48 to 72 hours following phone verification. Once executed, deletion is permanent and cannot be undone.',
    },
    {
      title: '5. Third-Party Messaging & Meta WhatsApp Data',
      content:
        'BloodConnect does not retain copies of your messages on external advertising platforms. Once your account is deleted from BloodConnect, our servers will never trigger any future WhatsApp or SMS messages to your phone number. Any chat history remaining inside your personal WhatsApp app is stored locally on your device and can be cleared using your WhatsApp device settings.',
    },
    {
      title: '6. Support & Inquiries',
      content:
        'For assistance with data deletion, contact platform support through the official BloodConnect portal.',
    },
  ],
};

export default function DataDeletionPage() {
  const [doc, setDoc] = useState<LegalDocument>(FALLBACK_DATA_DELETION_DOC);

  useEffect(() => {
    api
      .getDataDeletionInstructions()
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
          <span className="text-xs font-semibold px-3 py-1 bg-rose-100 text-rose-800 rounded-full">
            Effective: {doc.last_updated}
          </span>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-4">
          <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mb-2">
            <Trash2 className="w-6 h-6" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            {doc.title}
          </h1>
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
            {doc.summary}
          </p>

          {/* Key Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100 mt-6">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <UserX className="w-5 h-5 text-rose-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Total Removal</h4>
              <p className="text-xs text-slate-500 mt-1">Profile and phone number purged from databases.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <Clock className="w-5 h-5 text-amber-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">48-72h Turnaround</h4>
              <p className="text-xs text-slate-500 mt-1">Promptly processed upon OTP verification.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Zero Cost</h4>
              <p className="text-xs text-slate-500 mt-1">Free, unconditional user data erasure.</p>
            </div>
          </div>
        </div>

        {/* Sections Content */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-8">
          {doc.sections.map((section, idx) => (
            <div key={idx} className="space-y-3 pb-6 border-b border-slate-100 last:border-0 last:pb-0">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-rose-600 flex-shrink-0" />
                <span>{section.title}</span>
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                {section.content}
              </p>
              {section.points && section.points.length > 0 && (
                <ul className="space-y-2 pt-1 pl-2">
                  {section.points.map((pt, pIdx) => (
                    <li key={pIdx} className="text-xs sm:text-sm text-slate-600 flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
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
          <p>© {new Date().getFullYear()} {doc.platform_name} — User Data Rights & Transparency.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy-policy" className="hover:text-red-600 font-semibold transition-colors">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-red-600 font-semibold transition-colors">
              Terms of Service
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
