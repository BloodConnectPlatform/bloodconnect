'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { X, Phone, KeyRound, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

interface AuthModalProps {
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const router = useRouter();
  const { isLoginModalOpen, closeLoginModal, login } = useAuth();

  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
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
      const user = await login(formatted, otpCode.trim());
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
            className="absolute top-4 right-4 text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-12 h-12 bg-white/15 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs">
            {step === 'PHONE' ? <Phone className="w-6 h-6 text-white" /> : <KeyRound className="w-6 h-6 text-white" />}
          </div>
          <h3 className="text-xl font-bold">
            {step === 'PHONE' ? 'Sign In with Mobile' : 'Verify Mobile OTP'}
          </h3>
          <p className="text-xs text-rose-100 mt-1">
            {step === 'PHONE'
              ? 'Enter your phone number to receive a one-time login passcode.'
              : `Enter the 6-digit code sent to ${mobileNumber}`}
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6">
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
            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Mobile Number
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-slate-500">
                    +91
                  </span>
                  <input
                    type="tel"
                    maxLength={10}
                    placeholder="9876543210"
                    value={mobileNumber.replace(/^\+91/, '')}
                    onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, ''))}
                    required
                    className="w-full pl-12 pr-4 py-2.5 text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all placeholder:text-slate-400 font-medium"
                  />
                </div>
                <p className="text-[11px] text-slate-500 mt-1.5">
                  We use secure passwordless SMS verification. No password needed.
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading || mobileNumber.length < 10}
                className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-semibold text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  'Send One-Time Passcode'
                )}
              </button>

              <div className="text-center pt-2">
                <p className="text-xs text-slate-500">
                  New voluntary donor?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      closeLoginModal();
                      router.push('/register');
                    }}
                    className="text-red-600 font-semibold hover:underline"
                  >
                    Register as Donor
                  </button>
                </p>
              </div>
            </form>
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
                  className="w-full text-center tracking-[0.5em] text-lg font-bold py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-hidden transition-all placeholder:tracking-normal placeholder:font-normal placeholder:text-sm text-slate-800"
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
                  <span className="text-slate-400">Resend OTP in {cooldown}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    className="text-red-600 font-semibold hover:underline"
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
