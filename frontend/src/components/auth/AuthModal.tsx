'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import {
  X,
  MessageCircle,
  ArrowRight,
} from 'lucide-react';
import { redirectToWhatsAppLogin } from '@/lib/whatsapp';

interface AuthModalProps {
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = () => {
  const router = useRouter();
  const { isLoginModalOpen, closeLoginModal } = useAuth();

  if (!isLoginModalOpen) return null;

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
            Sign In to BloodConnect
          </h3>
          <p className="text-xs text-rose-100 mt-1 font-medium">
            Instant 1-Click WhatsApp authentication to access your account.
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
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

          {/* Clean Footer Link */}
          <div className="text-center pt-2">
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
      </div>
    </div>
  );
};
