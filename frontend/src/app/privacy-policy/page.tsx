'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Shield,
  Lock,
  EyeOff,
  CheckCircle2,
  PhoneCall,
  Clock,
  ArrowLeft,
  AlertTriangle,
  FileText,
  HeartHandshake,
} from 'lucide-react';
import { api } from '@/lib/api';
import { LegalDocument } from '@/types';

const FALLBACK_PRIVACY_DOC: LegalDocument = {
  title: 'Privacy Policy',
  last_updated: 'September 2026',
  platform_name: 'BloodConnect',
  summary:
    'BloodConnect is a non-profit, voluntary blood donor discovery platform operating across Coimbatore and surrounding regions. We enforce strict privacy guarantees: donor phone numbers are never published in public search directories, and contact numbers are exchanged only when a donor explicitly accepts an emergency blood request.',
  sections: [
    {
      title: '1. Scope & Core Privacy Commitment',
      content:
        'This Privacy Policy describes how BloodConnect collects, uses, and safeguards personal data when voluntary donors and requesters use our platform. BloodConnect operates strictly as an intermediary communication directory to connect voluntary blood donors with patients in medical emergencies. We respect individual privacy, enforce role-based data isolation, and never monetize, sell, or rent personal information to any third party.',
      points: [
        'Applicable to all users across covered regions including Coimbatore, Sulur, Tiruppur, Pollachi, Mettupalayam, Avinashi, Palladam, Udumalpet, Annur, Madukkarai, and Perur.',
        'Designed with privacy-by-design principles: data is collected solely for facilitating voluntary blood donations.',
      ],
    },
    {
      title: '2. Information We Collect',
      content:
        'We collect only the minimal data strictly necessary to facilitate verified emergency blood donation connections.',
      points: [
        'Voluntary Donors: Full name, 10-digit Indian mobile number, blood group (A+, A-, B+, B-, AB+, AB-, O+, O-), date of birth (to verify legal eligibility between 18 and 65 years old), location (predefined district/locality), availability status, and contact consent.',
        'Blood Requesters: Full name, 10-digit mobile number, patient name, hospital name, required blood group, urgency level, location, and optional medical requirement details.',
        'Authentication Data: Hashed One-Time Passwords (OTPs) and cryptographically signed session tokens (JWT). Plaintext OTPs and passwords are never stored in our database.',
        'Audit & Security Logs: Administrative action records and dispute/report submissions for platform moderation and safety.',
      ],
    },
    {
      title: '3. Public Directory vs. Contact Privacy Protection',
      content:
        'BloodConnect enforces strict data segregation between public search results and private contact information.',
      points: [
        'Concealed Public Search: Public donor search results display ONLY the donor\'s name, blood group, general location, age, and availability status. Donor mobile numbers are strictly hidden from public searches and unauthenticated API queries.',
        'Pending Requests: When a requester submits a donation request, the requester\'s mobile number is concealed from the donor while the request remains in PENDING status.',
        'Two-Way Contact Disclosure Upon Acceptance: Contact phone numbers of the donor and requester are revealed to each other ONLY after the donor explicitly accepts (ACCEPTED) the emergency blood request.',
        'Rejected or Inactive Requests: If a request is declined or cancelled, phone numbers remain permanently hidden between the parties.',
      ],
    },
    {
      title: '4. OTP Verification & Passwordless Authentication',
      content:
        'BloodConnect utilizes a passwordless authentication model using 6-digit One-Time Passwords (OTPs) delivered via WhatsApp or SMS.',
      points: [
        'Server-Side Hashing: OTPs are hashed using SHA-256 before being stored in the database. Plaintext OTPs are never stored or logged.',
        'Time-Limited Expiry: Each OTP is valid for a maximum of 5 minutes.',
        'Brute-Force Protection: A maximum of 3 failed verification attempts is allowed before the OTP is invalidated. Resend requests enforce a 60-second cooldown.',
      ],
    },
    {
      title: '5. Third-Party Messaging Services (Meta WhatsApp & SMS)',
      content:
        'To deliver critical, time-sensitive alerts during medical emergencies, BloodConnect integrates with the Meta WhatsApp Cloud API and transactional SMS gateways.',
      points: [
        'Transactional Messages Only: WhatsApp notifications are strictly restricted to authentication OTPs, magic login verification links, and urgent blood request notifications.',
        'No Marketing or Advertising: We do not send promotional broadcasts, advertisements, or unsolicited messages.',
        'Meta Cloud API: Messages sent through WhatsApp adhere to Meta\'s Cloud API platform policies. We share only the recipient\'s phone number and the necessary transactional message parameters.',
      ],
    },
    {
      title: '6. User Rights & Data Management',
      content:
        'Users maintain full control over their data and availability on BloodConnect.',
      points: [
        'Availability Toggle: Donors can toggle their availability status to "Unavailable" at any moment via their dashboard to stop receiving donation requests.',
        'Profile Updates: Donors can update their name, location, and contact consent directly from their account settings.',
        'Reporting & Moderation: Users can report incorrect profiles, misuse, or spam through the built-in reporting system for administrative investigation.',
      ],
    },
    {
      title: '7. Data Security & Storage',
      content:
        'We implement robust technical and operational measures to protect your personal information against unauthorized access, alteration, or disclosure. Data is stored in secured databases with role-based access control, parameterized queries, and administrative audit logging.',
    },
    {
      title: '8. Contact Information',
      content:
        'If you have questions, feedback, or concerns regarding this Privacy Policy or your data on BloodConnect, you may contact the platform administrators through the official community channels.',
    },
  ],
};

export default function PrivacyPolicyPage() {
  const [doc, setDoc] = useState<LegalDocument>(FALLBACK_PRIVACY_DOC);

  useEffect(() => {
    api
      .getPrivacyPolicy()
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
          <span className="text-xs font-semibold px-3 py-1 bg-red-100 text-red-700 rounded-full">
            Effective: {doc.last_updated}
          </span>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-4">
          <div className="w-12 h-12 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center mb-2">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            {doc.title}
          </h1>
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
            {doc.summary}
          </p>

          {/* Key Privacy Highlights Card */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100 mt-6">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <EyeOff className="w-5 h-5 text-red-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Hidden Mobile</h4>
              <p className="text-xs text-slate-500 mt-1">Never shown in public search results.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <HeartHandshake className="w-5 h-5 text-emerald-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Explicit Consent</h4>
              <p className="text-xs text-slate-500 mt-1">Phone numbers shared only on request acceptance.</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <Lock className="w-5 h-5 text-blue-600 mb-2" />
              <h4 className="text-xs font-bold text-slate-900 uppercase">Hashed OTPs</h4>
              <p className="text-xs text-slate-500 mt-1">No passwords, SHA-256 OTPs with 5m expiry.</p>
            </div>
          </div>
        </div>

        {/* Sections Content */}
        <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-8">
          {doc.sections.map((section, idx) => (
            <div key={idx} className="space-y-3 pb-6 border-b border-slate-100 last:border-0 last:pb-0">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-red-600 flex-shrink-0" />
                <span>{section.title}</span>
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                {section.content}
              </p>
              {section.points && section.points.length > 0 && (
                <ul className="space-y-2 pt-1 pl-2">
                  {section.points.map((pt, pIdx) => (
                    <li key={pIdx} className="text-xs sm:text-sm text-slate-600 flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
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
          <p>© {new Date().getFullYear()} {doc.platform_name} — Voluntary & Privacy-First Platform.</p>
          <div className="flex items-center gap-4">
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
