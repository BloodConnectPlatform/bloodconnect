'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { AlertCircle, ArrowRight, CheckCircle2, Loader2 } from 'lucide-react';
import Link from 'next/link';

function WhatsAppAuthHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const { refreshUser } = useAuth();

  const [statusState, setStatusState] = useState<'LOADING' | 'SUCCESS' | 'ERROR'>('LOADING');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function handleRedeem() {
      if (!token) {
        if (isMounted) {
          setStatusState('ERROR');
          setErrorMessage('No login token provided in the link.');
        }
        return;
      }

      try {
        const authData = await api.redeemWhatsAppToken(token);
        await refreshUser();

        if (isMounted) {
          setStatusState('SUCCESS');
          const role = authData.user.role;
          if (role === 'ADMIN') {
            router.replace('/admin');
          } else if (role === 'DONOR') {
            router.replace('/donor/dashboard');
          } else {
            router.replace('/requester/dashboard');
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setStatusState('ERROR');
          setErrorMessage(
            err.message || 'This login link is invalid or has expired. Please request a new login link through WhatsApp.'
          );
        }
      }
    }

    handleRedeem();

    return () => {
      isMounted = false;
    };
  }, [token, router, refreshUser]);

  return (
    <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden text-center">
      <div className="bg-gradient-to-r from-red-600 to-rose-700 p-8 text-white">
        <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs p-1.5 border border-white/20 shadow-md">
          <Image
            src="/logo-icon.png"
            alt="Blood Connect"
            width={46}
            height={46}
            className="object-contain"
          />
        </div>
        <h2 className="text-2xl font-black">WhatsApp Fast Login</h2>
        <p className="text-xs text-rose-100 mt-1">One-time secure authentication link</p>
      </div>

      <div className="p-8 space-y-6">
        {statusState === 'LOADING' && (
          <div className="py-6 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-10 h-10 text-red-600 animate-spin" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-800">Verifying your login link...</h3>
              <p className="text-xs text-slate-500">Securing your session with Blood Connect.</p>
            </div>
          </div>
        )}

        {statusState === 'SUCCESS' && (
          <div className="py-6 flex flex-col items-center justify-center space-y-4">
            <CheckCircle2 className="w-10 h-10 text-green-600" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-800">Login Successful!</h3>
              <p className="text-xs text-slate-500">Redirecting to your dashboard...</p>
            </div>
          </div>
        )}

        {statusState === 'ERROR' && (
          <div className="space-y-6">
            <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-3 text-left">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-red-800 mb-1">Login Link Invalid or Expired</h4>
                <p className="text-xs text-red-700 leading-relaxed">
                  {errorMessage || 'This login link is invalid or has expired. Please request a new login link through WhatsApp.'}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <Link
                href="/login"
                className="w-full py-3.5 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
              >
                <span>Go to Standard Login</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/"
                className="block text-xs font-semibold text-slate-500 hover:text-slate-800"
              >
                Back to Home
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WhatsAppAuthPage() {
  return (
    <div className="flex-1 bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6">
      <Suspense
        fallback={
          <div className="w-full max-w-md bg-white rounded-3xl p-8 text-center shadow-md">
            <Loader2 className="w-8 h-8 text-red-600 animate-spin mx-auto" />
            <p className="text-sm text-slate-500 mt-2 font-medium">Loading authentication...</p>
          </div>
        }
      >
        <WhatsAppAuthHandler />
      </Suspense>
    </div>
  );
}
