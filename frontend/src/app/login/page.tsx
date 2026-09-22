'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import {
  Phone,
  KeyRound,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Heart,
  ArrowRight,
  User as UserIcon,
  MessageCircle,
} from 'lucide-react';
import Link from 'next/link';
import { redirectToWhatsAppLogin } from '@/lib/whatsapp';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, user, login, authenticateRequester } = useAuth();

  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [fullName, setFullName] = useState('');
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
      if (res.debug_otp) {
        setOtpCode(res.debug_otp);
      }
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
      let loggedUser;
      if (fullName.trim()) {
        loggedUser = await authenticateRequester(fullName.trim(), formatted, otpCode.trim());
      } else {
        loggedUser = await login(formatted, otpCode.trim());
      }
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
            {step === 'PHONE' ? 'Sign In to BloodConnect' : 'Verify Mobile OTP'}
          </h1>
          <p className="text-xs text-rose-100 mt-1 font-medium">
            {step === 'PHONE'
              ? 'Enter your mobile number to access your account or send requests.'
              : `Enter the 6-digit code sent to ${mobileNumber}`}
          </p>
        </div>

        {/* Body */}
        <div className="p-8 space-y-5">
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 font-semibold">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'PHONE' ? (
            <div className="space-y-5">
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
                    Verify in seconds without waiting for SMS codes or typing passwords.
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

              {/* Divider */}
              <div className="relative flex items-center justify-center pt-1">
                <div className="border-t border-slate-200 w-full" />
                <span className="bg-white px-3 text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0">
                  Or sign in with SMS OTP
                </span>
                <div className="border-t border-slate-200 w-full" />
              </div>

              {/* SECONDARY: Mobile Number Form */}
              <form onSubmit={handleSendOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Mobile Number *
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-600">
                      +91
                    </span>
                    <input
                      type="tel"
                      maxLength={10}
                      placeholder="Enter 10-digit mobile"
                      value={mobileNumber.replace(/^\+91/, '')}
                      onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, ''))}
                      required
                      className="w-full pl-12 pr-4 py-3 text-sm text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden font-bold placeholder:font-normal placeholder:text-slate-400 min-h-[44px]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Full Name <span className="text-slate-400 font-normal lowercase">(optional for existing users)</span>
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="e.g. Ramesh Kumar"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 text-sm text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden font-medium placeholder:text-slate-400 min-h-[44px]"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || mobileNumber.length < 10}
                  className="w-full py-3.5 px-4 bg-slate-900 hover:bg-black active:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed min-h-[46px]"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Sending SMS Code...</span>
                    </>
                  ) : (
                    <>
                      <span>Send SMS Verification Code</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </form>

              <div className="text-center pt-1">
                <p className="text-xs text-slate-500 font-medium">
                  Want to donate blood?{' '}
                  <Link href="/register" className="text-red-600 font-bold hover:underline">
                    Register as Voluntary Donor
                  </Link>
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleVerifyLogin} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 text-center">
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
                  className="w-full text-center tracking-[0.5em] text-2xl font-black py-3.5 text-slate-900 bg-white border border-slate-300 rounded-xl font-mono focus:ring-2 focus:ring-red-500 outline-hidden placeholder:text-slate-400 min-h-[48px]"
                />
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <button
                  type="button"
                  onClick={() => setStep('PHONE')}
                  className="text-slate-500 hover:text-slate-800 font-bold cursor-pointer"
                >
                  Change Number
                </button>
                {cooldown > 0 ? (
                  <span className="text-slate-400 font-medium">Resend code in {cooldown}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    className="text-red-600 font-bold hover:underline cursor-pointer"
                  >
                    Resend OTP
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading || otpCode.length !== 6}
                className="w-full py-3.5 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer min-h-[46px]"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
