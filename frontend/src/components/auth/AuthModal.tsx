'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import {
  X,
  Phone,
  KeyRound,
  Loader2,
  AlertCircle,
  CheckCircle2,
  User as UserIcon,
  MessageCircle,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { redirectToWhatsAppLogin } from '@/lib/whatsapp';

interface AuthModalProps {
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const router = useRouter();
  const { isLoginModalOpen, closeLoginModal, login, authenticateRequester } = useAuth();

  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [fullName, setFullName] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldown]);

  useEffect(() => {
    if (!isLoginModalOpen) {
      setStep('PHONE');
      setFullName('');
      setMobileNumber('');
      setOtpCode('');
      setError(null);
      setSuccessMsg(null);
      setCooldown(0);
    }
  }, [isLoginModalOpen]);

  if (!isLoginModalOpen) return null;

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
    setSuccessMsg(null);

    const formatted = normalizePhone(mobileNumber);
    if (!/^\+91[6-9]\d{9}$/.test(formatted)) {
      setError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.sendOtp(formatted, 'LOGIN');
      setStep('OTP');
      setSuccessMsg(res.message || 'OTP sent successfully!');
      setCooldown(res.cooldown_seconds || 60);
      if (res.debug_otp) {
        setOtpCode(res.debug_otp);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (otpCode.trim().length !== 6) {
      setError('Please enter a valid 6-digit OTP code');
      return;
    }

    setIsLoading(true);
    try {
      const formatted = normalizePhone(mobileNumber);
      let user;
      if (fullName.trim()) {
        user = await authenticateRequester(fullName.trim(), formatted, otpCode.trim());
      } else {
        user = await login(formatted, otpCode.trim());
      }

      closeLoginModal();
      if (onSuccess) {
        onSuccess();
      } else {
        const hasPending = typeof window !== 'undefined' && localStorage.getItem('bloodconnect_pending_request');
        if (hasPending) {
          router.push('/find-donor');
        } else if (user.role === 'ADMIN') {
          router.push('/admin');
        } else if (user.role === 'DONOR') {
          router.push('/donor/dashboard');
        } else {
          router.push('/requester/dashboard');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden max-h-[92vh] flex flex-col">
        
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 p-6 text-white text-center relative shrink-0">
          <button
            onClick={closeLoginModal}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-2 rounded-full hover:bg-white/15 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-2.5 backdrop-blur-xs p-1.5 border border-white/20 shadow-md">
            <Image
              src="/logo-icon.png"
              alt="Blood Connect"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>

          <h3 className="text-xl font-black tracking-tight">
            {step === 'PHONE' ? 'Sign In to BloodConnect' : 'Verify Mobile OTP'}
          </h3>
          <p className="text-xs text-rose-100 mt-1 font-medium">
            {step === 'PHONE'
              ? 'Enter your mobile number to access your account or send requests.'
              : `Enter the 6-digit code sent to ${mobileNumber}`}
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 font-semibold">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-2.5 text-xs text-emerald-700 font-semibold">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {step === 'PHONE' ? (
            <div className="space-y-4">
              {/* PRIMARY: WhatsApp 1-Click Sign In */}
              <div className="p-4 bg-emerald-50/90 border-2 border-emerald-300 rounded-2xl space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-black uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Fastest • Recommended</span>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-700">Instant Access</span>
                </div>

                <div>
                  <h4 className="text-sm font-black text-slate-900 flex items-center gap-2">
                    <MessageCircle className="w-4 h-4 text-emerald-600 fill-emerald-600/20" />
                    <span>1-Click Sign In via WhatsApp</span>
                  </h4>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    Verify in seconds without waiting for SMS codes or typing passwords.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    closeLoginModal();
                    redirectToWhatsAppLogin('LOGIN');
                  }}
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
              <form onSubmit={handleSendOtp} className="space-y-3.5">
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
                  className="w-full py-3 px-4 bg-slate-900 hover:bg-black active:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed min-h-[44px]"
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

              {/* Clean Footer Link */}
              <div className="text-center pt-1">
                <p className="text-xs text-slate-500 font-medium">
                  Looking to donate blood?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      closeLoginModal();
                      router.push('/register');
                    }}
                    className="text-red-600 font-bold hover:underline cursor-pointer"
                  >
                    Register as Donor
                  </button>
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleVerifyLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 text-center">
                  Enter 6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="• • • • • •"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  className="w-full text-center tracking-[0.5em] text-2xl font-black py-3.5 text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all font-mono min-h-[48px]"
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
                  <span className="text-slate-400 font-medium">Resend OTP in {cooldown}s</span>
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
                className="w-full py-3.5 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed min-h-[46px]"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Continue</span>
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
};
