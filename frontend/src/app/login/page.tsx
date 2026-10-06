'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import {
  Loader2,
  Heart,
  ArrowRight,
  MessageCircle,
} from 'lucide-react';
import Link from 'next/link';
import { redirectToWhatsAppLogin } from '@/lib/whatsapp';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get('redirect');
  const { isAuthenticated, user } = useAuth();

  const [pendingRequest, setPendingRequest] = useState<any>(null);

  // Check for pending request from find-donor flow
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('bloodconnect_pending_request');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.donor) {
            setPendingRequest(parsed);
          }
        }
      } catch {}
    }
  }, [searchParams]);

  const getRedirectTarget = (role?: string) => {
    const hasPending = typeof window !== 'undefined' && localStorage.getItem('bloodconnect_pending_request');
    if (redirectParam) return redirectParam;
    if (hasPending) return '/find-donor';
    if (role === 'ADMIN') return '/admin';
    if (role === 'DONOR') return '/donor/dashboard';
    return '/requester/dashboard';
  };

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(getRedirectTarget(user?.role));
    }
  }, [isAuthenticated, user, router, redirectParam]);

  return (
    <div className="flex-1 bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 p-8 text-white text-center">
          <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs p-1.5 border border-white/20 shadow-md">
            <Image
              src="/logo-icon.png"
              alt="Blood Connect"
              width={46}
              height={46}
              className="object-contain"
            />
          </div>
          <h1 className="text-2xl font-black tracking-tight">
            Sign In to BloodConnect
          </h1>
          <p className="text-xs text-rose-100 mt-1 font-medium">
            {pendingRequest
              ? 'Fast 1-Click WhatsApp verification to complete and send your blood request.'
              : 'Instant 1-Click WhatsApp authentication to access your account.'}
          </p>
        </div>

        {/* Body */}
        <div className="p-8 space-y-5">
          {pendingRequest && (
            <div className="p-4 bg-rose-50 border-2 border-rose-200 rounded-2xl flex items-start gap-3 text-xs text-rose-900 animate-in fade-in">
              <Heart className="w-5 h-5 text-rose-600 shrink-0 mt-0.5 fill-rose-600" />
              <div className="space-y-1">
                <div className="font-bold text-rose-950 text-sm">
                  Blood Request Saved & Ready
                </div>
                <p className="text-rose-800 leading-relaxed">
                  Requesting <strong>{pendingRequest.required_units || 1} unit(s)</strong> from donor{' '}
                  <strong>{pendingRequest.donor?.full_name} ({pendingRequest.donor?.blood_group})</strong> for{' '}
                  <strong>{pendingRequest.patient_name || 'Patient'}</strong> at {pendingRequest.hospital_name}.
                </p>
                <p className="text-[11px] text-rose-700 font-medium">
                  Verify via WhatsApp below to automatically return and send your request with 1 tap.
                </p>
              </div>
            </div>
          )}

          {/* PRIMARY: WhatsApp 1-Click Sign In */}
          <div className="p-5 bg-emerald-50/90 border-2 border-emerald-300 rounded-2xl space-y-3 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-black uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>Fastest • Recommended</span>
              </div>
              <span className="text-xs font-bold text-emerald-700">Instant Access</span>
            </div>

            <div>
              <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-emerald-600 fill-emerald-600/20" />
                <span>1-Click Sign In via WhatsApp</span>
              </h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Verify in seconds without waiting for SMS OTP codes or typing passwords.
              </p>
            </div>

            <button
              type="button"
              onClick={() => redirectToWhatsAppLogin('LOGIN')}
              className="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-black text-sm rounded-xl shadow-md hover:shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2.5 cursor-pointer min-h-[46px]"
            >
              <MessageCircle className="w-5 h-5 fill-white" />
              <span>CONTINUE WITH WHATSAPP</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="text-center pt-2">
            <p className="text-xs text-slate-500 font-medium">
              Want to donate blood?{' '}
              <Link href="/register" className="text-red-600 font-bold hover:underline">
                Register as Voluntary Donor
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 bg-slate-50 flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
