'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { Phone, KeyRound, Loader2, AlertCircle, CheckCircle2, Heart, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, user, login } = useAuth();

  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (isAuthenticated) {
      if (user?.role === 'ADMIN') router.push('/admin');
      else if (user?.role === 'DONOR') router.push('/donor/dashboard');
      else router.push('/requester/dashboard');
    }
  }, [isAuthenticated, user, router]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldown]);

  const normalizePhone = (num: string) => {
    const cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return `+91${cleaned}`;
    if (cleaned.length === 12 && cleaned.startsWith('91')) return `+${cleaned}`;
    if (num.startsWith('+91') && cleaned.length === 12) return num;
    return `+91${cleaned}`;
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const formatted = normalizePhone(mobileNumber);
    if (!/^\+91[6-9]\d{9}$/.test(formatted)) {
      setError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.sendOtp(formatted, 'LOGIN');
      setStep('OTP');
      setCooldown(res.cooldown_seconds || 60);
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (otpCode.trim().length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setIsLoading(true);
    try {
      const formatted = normalizePhone(mobileNumber);
      const loggedUser = await login(formatted, otpCode.trim());
      if (loggedUser.role === 'ADMIN') {
        router.push('/admin');
      } else if (loggedUser.role === 'DONOR') {
        router.push('/donor/dashboard');
      } else {
        router.push('/requester/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
        <div className="bg-gradient-to-r from-red-600 to-rose-700 p-8 text-white text-center">
          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs">
            {step === 'PHONE' ? <Phone className="w-6 h-6 text-white" /> : <KeyRound className="w-6 h-6 text-white" />}
          </div>
          <h2 className="text-2xl font-black">
            {step === 'PHONE' ? 'Simple Login' : 'Verify Mobile OTP'}
          </h2>
          <p className="text-xs text-rose-100 mt-1">
            {step === 'PHONE'
              ? 'Enter your name and mobile number to access Blood Connect.'
              : `Enter the 6-digit code sent to ${mobileNumber}`}
          </p>
        </div>

        <div className="p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'PHONE' ? (
            <form onSubmit={handleSendOtp} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Your Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full px-4 py-3 text-sm border border-slate-300 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Mobile Number *
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-500">
                    +91
                  </span>
                  <input
                    type="tel"
                    maxLength={10}
                    placeholder="9876543210"
                    value={mobileNumber.replace(/^\+91/, '')}
                    onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, ''))}
                    required
                    autoFocus
                    className="w-full pl-14 pr-4 py-3 text-sm border border-slate-300 rounded-xl font-bold text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || mobileNumber.length < 10}
                className="w-full py-3.5 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  <>
                    <span>Login</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <p className="text-xs text-slate-500">
                  Want to donate blood?{' '}
                  <Link href="/register" className="text-red-600 font-bold hover:underline">
                    Register as Donor
                  </Link>
                </p>
              </div>
            </form>
          ) : (
            <form onSubmit={handleVerifyLogin} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="• • • • • •"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  className="w-full text-center tracking-[0.5em] text-2xl font-bold py-3 border border-slate-300 rounded-xl font-mono text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => setStep('PHONE')}
                  className="text-slate-500 hover:text-slate-800 font-medium"
                >
                  Change Number
                </button>
                {cooldown > 0 ? (
                  <span className="text-slate-400">Resend code in {cooldown}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    className="text-red-600 font-bold hover:underline"
                  >
                    Resend OTP
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading || otpCode.length !== 6}
                className="w-full py-3.5 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify & Sign In'
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
