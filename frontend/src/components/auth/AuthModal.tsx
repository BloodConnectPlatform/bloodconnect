'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { X, Phone, KeyRound, Loader2, AlertCircle, CheckCircle2, User as UserIcon, MessageCircle } from 'lucide-react';
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
      setError('Please enter a valid 6-digit OTP');
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
        if (user.role === 'ADMIN') {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-red-600 to-rose-700 p-6 text-white text-center relative">
          <button
            onClick={closeLoginModal}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs p-1.5 border border-white/20 shadow-md">
            <Image
              src="/logo-icon.png"
              alt="Blood Connect"
              width={46}
              height={46}
              className="object-contain"
            />
          </div>
          <h3 className="text-xl font-bold">
            {step === 'PHONE' ? 'Sign In / Quick Requester Sign Up' : 'Verify Mobile OTP'}
          </h3>
          <p className="text-xs text-rose-100 mt-1">
            {step === 'PHONE'
              ? 'Enter your mobile number and name to sign in or request blood.'
              : `Enter the 6-digit code sent to ${mobileNumber}`}
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">
          {/* Quick Demo Helper (development only) */}
          {(process.env.NODE_ENV !== 'production' || process.env.NEXT_PUBLIC_SHOW_DEMO_ACCOUNTS === 'true') && (
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-600 space-y-1">
              <div className="font-bold text-slate-800">Quick Test Accounts:</div>
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setMobileNumber('9876543220');
                    setFullName('Priya Sharma');
                  }}
                  className="px-2 py-0.5 bg-rose-100 text-rose-800 rounded font-bold hover:bg-rose-200 cursor-pointer"
                >
                  Requester (9876543220)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMobileNumber('9876543201');
                    setFullName('Arun Kumar');
                  }}
                  className="px-2 py-0.5 bg-red-100 text-red-800 rounded font-bold hover:bg-red-200 cursor-pointer"
                >
                  Donor (9876543201)
                </button>
              </div>
            </div>
          )}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs text-emerald-700">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {step === 'PHONE' ? (
            <div className="space-y-4">
              {/* Primary WhatsApp Fast Login Button */}
              <div className="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-4 text-center space-y-2.5">
                <div className="flex items-center justify-center gap-2 text-emerald-900 font-extrabold text-sm">
                  <MessageCircle className="w-4 h-4 text-emerald-600" />
                  <span>Fast WhatsApp Authentication</span>
                </div>
                <p className="text-xs text-emerald-700 leading-relaxed">
                  Sends <span className="font-mono font-bold bg-white px-1.5 py-0.5 rounded border border-emerald-300 text-emerald-900">LOGIN</span> to our WhatsApp number to receive an instant single-use magic login link.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    closeLoginModal();
                    redirectToWhatsAppLogin('LOGIN');
                  }}
                  className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>Open WhatsApp &amp; Send LOGIN</span>
                </button>
              </div>

              {/* SMS OTP - Disabled & Marked Coming Soon */}
              <div className="pt-1">
                <div className="relative flex items-center justify-center mb-3">
                  <div className="border-t border-slate-200 w-full" />
                  <div className="bg-white px-3 flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      SMS OTP Sign In
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-black bg-amber-100 text-amber-800 border border-amber-300">
                      Coming Soon
                    </span>
                  </div>
                  <div className="border-t border-slate-200 w-full" />
                </div>

                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3 opacity-60">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">
                      Mobile Number
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-slate-400">
                        +91
                      </span>
                      <input
                        type="tel"
                        disabled
                        placeholder="9876543210"
                        value=""
                        className="w-full pl-11 pr-4 py-2 text-sm text-slate-500 bg-slate-100 border border-slate-200 rounded-lg cursor-not-allowed font-medium"
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    disabled
                    className="w-full py-2.5 px-4 bg-slate-200 text-slate-400 font-semibold text-xs rounded-xl cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <span>SMS Verification Unavailable (Coming Soon)</span>
                  </button>

                  <p className="text-[10px] text-slate-500 text-center leading-tight">
                    Direct SMS OTP verification is undergoing carrier upgrades. Please use instant WhatsApp login above.
                  </p>
                </div>
              </div>

              <div className="text-center pt-1">
                <p className="text-xs text-slate-500">
                  New voluntary donor?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      closeLoginModal();
                      router.push('/register');
                    }}
                    className="text-red-600 font-semibold hover:underline cursor-pointer"
                  >
                    Register as Donor
                  </button>
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleVerifyLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Enter 6-Digit OTP
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="• • • • • •"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  className="w-full text-center tracking-[0.5em] text-lg font-bold py-2.5 text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all placeholder:tracking-normal placeholder:font-normal placeholder:text-sm placeholder:text-slate-400"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => setStep('PHONE')}
                  className="text-slate-500 hover:text-slate-800 font-medium cursor-pointer"
                >
                  Change Number
                </button>
                {cooldown > 0 ? (
                  <span className="text-slate-400">Resend OTP in {cooldown}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    className="text-red-600 font-semibold hover:underline cursor-pointer"
                  >
                    Resend OTP
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading || otpCode.length !== 6}
                className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-semibold text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify & Log In'
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
