'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { AlertCircle, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function WhatsAppCallbackPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();

  const [statusState, setStatusState] = useState<'LOADING' | 'SUCCESS' | 'ERROR'>('LOADING');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function handleCallback() {
      try {
        // Read the base64-encoded auth payload from the URL hash fragment
        const hash = window.location.hash?.slice(1); // Remove the leading '#'
        if (!hash) {
          if (isMounted) {
            setStatusState('ERROR');
            setErrorMessage('No authentication data found in the link. Please request a new login link through WhatsApp.');
          }
          return;
        }

        // Decode the base64url payload
        const jsonStr = atob(hash.replace(/-/g, '+').replace(/_/g, '/'));
        const payload = JSON.parse(jsonStr);

        const { access_token, refresh_token, user, redirect } = payload;

        if (!access_token || !refresh_token || !user) {
          throw new Error('Incomplete authentication data received.');
        }

        // Store tokens and user in localStorage (now on the correct frontend domain)
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('bloodconnect_user', JSON.stringify(user));

        // Clear the hash fragment from the URL for security
        window.history.replaceState(null, '', window.location.pathname);

        // Refresh the auth context so the app recognizes the session
        await refreshUser();

        if (isMounted) {
          setStatusState('SUCCESS');

          // Redirect to find-donor if pending request exists, otherwise to redirect or home
          const hasPending = typeof window !== 'undefined' && localStorage.getItem('bloodconnect_pending_request');
          const targetPath = hasPending ? '/find-donor' : (redirect || '/');
          router.replace(targetPath);
        }
      } catch (err: any) {
        console.error('WhatsApp callback error:', err);
        if (isMounted) {
          setStatusState('ERROR');
          setErrorMessage(
            err.message || 'Failed to process the login link. Please request a new login link through WhatsApp.'
          );
        }
      }
    }

    handleCallback();

    return () => {
      isMounted = false;
    };
  }, [router, refreshUser]);

  return (
    <div className="flex-1 bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6">
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
          <p className="text-xs text-rose-100 mt-1">Secure cross-domain authentication</p>
        </div>

        <div className="p-8 space-y-6">
          {statusState === 'LOADING' && (
            <div className="py-6 flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-red-600 animate-spin" />
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-800">Signing you in...</h3>
                <p className="text-xs text-slate-500">Setting up your secure session.</p>
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
                  <h4 className="text-xs font-bold text-red-800 mb-1">Authentication Error</h4>
                  <p className="text-xs text-red-700 leading-relaxed">
                    {errorMessage || 'Failed to process the login link. Please request a new login link through WhatsApp.'}
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <Link
                  href="/login"
                  className="w-full py-3.5 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
                >
                  <span>Go to Login</span>
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
    </div>
  );
}
