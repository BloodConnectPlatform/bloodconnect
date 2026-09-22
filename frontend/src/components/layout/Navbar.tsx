'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { openPlatformNotice } from '@/components/common/PlatformNoticeModal';
import {
  Heart,
  Droplet,
  Search,
  LayoutDashboard,
  LogOut,
  ShieldAlert,
  Menu,
  X,
  AlertTriangle,
  User as UserIcon,
  MessageCircle,
} from 'lucide-react';
import { redirectToWhatsAppLogin, fetchAndSyncWhatsAppConfig } from '@/lib/whatsapp';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, donorProfile, isAuthenticated, openLoginModal, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchAndSyncWhatsAppConfig();
    if (isAuthenticated) {
      api.getNotifications(1, 10).then((res) => {
        const unread = res.items.filter((n) => !n.is_read).length;
        setUnreadCount(unread);
      }).catch(() => {});
    }
  }, [isAuthenticated, pathname]);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-11 h-11 rounded-2xl bg-white border border-red-100 shadow-sm flex items-center justify-center p-1 group-hover:scale-105 group-hover:border-red-300 transition-all">
              <Image
                src="/logo-icon.png"
                alt="Blood Connect Logo"
                width={38}
                height={38}
                className="object-contain"
                priority
              />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-slate-900 flex items-center gap-1">
                Blood<span className="text-red-600">Connect</span>
              </span>
              <span className="block text-[10px] font-bold text-slate-500 -mt-1 tracking-wider uppercase">
                Coimbatore Network
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5 lg:gap-2">
            <Link
              href="/"
              className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors ${
                pathname === '/'
                  ? 'text-red-600 bg-red-50'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              Home
            </Link>

            <Link
              href="/find-donor"
              className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 ${
                pathname === '/find-donor'
                  ? 'text-red-600 bg-red-50'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              <Search className="w-4 h-4 text-red-600" />
              <span>Find a Donor</span>
            </Link>

            <Link
              href="/register"
              className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 ${
                pathname === '/register'
                  ? 'text-red-600 bg-red-50'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              <Heart className="w-4 h-4 text-red-500" />
              <span>Register as Donor</span>
            </Link>

            <button
              type="button"
              onClick={openPlatformNotice}
              className="px-3 py-2 rounded-xl text-xs sm:text-sm font-bold text-amber-800 hover:text-amber-950 hover:bg-amber-50/80 transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>Platform Notice</span>
            </button>

            {isAuthenticated && user?.role === 'ADMIN' && (
              <Link
                href="/admin"
                className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/admin')
                    ? 'text-purple-700 bg-purple-50'
                    : 'text-purple-600 hover:text-purple-700 hover:bg-purple-50/60'
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Admin</span>
              </Link>
            )}

            {isAuthenticated && user?.role === 'DONOR' && (
              <Link
                href="/donor/dashboard"
                className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/donor')
                    ? 'text-red-600 bg-red-50'
                    : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Donor Hub</span>
                {donorProfile?.is_available && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="Available for requests" />
                )}
              </Link>
            )}

            {isAuthenticated && user?.role === 'REQUESTER' && (
              <Link
                href="/requester/dashboard"
                className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/requester')
                    ? 'text-red-600 bg-red-50'
                    : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>My Requests</span>
              </Link>
            )}
          </nav>

          {/* Desktop Right Action Area: Single Clean Sign In / User Status */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-2.5">
                <div className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-100/90 rounded-xl text-xs font-bold text-slate-800 border border-slate-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-slate-900">{user?.name || 'User'}</span>
                  <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-black">
                    {user?.role}
                  </span>
                </div>

                <button
                  onClick={logout}
                  className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/register"
                  className="px-4 py-2 text-slate-700 hover:text-red-600 font-bold text-xs sm:text-sm hover:bg-slate-50 rounded-xl transition-colors flex items-center gap-1.5"
                >
                  <Heart className="w-4 h-4 text-red-500" />
                  <span>Register</span>
                </Link>

                <button
                  onClick={openLoginModal}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
                  title="Fast WhatsApp & Mobile Sign In"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>Sign In</span>
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-700 hover:text-red-600 rounded-xl hover:bg-slate-100 transition-colors"
              aria-label="Toggle Navigation"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-2">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-slate-800 hover:bg-slate-50"
          >
            Home
          </Link>
          <Link
            href="/find-donor"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-slate-800 hover:bg-slate-50"
          >
            <Search className="w-4 h-4 text-red-600" />
            Find a Donor
          </Link>
          <Link
            href="/register"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-slate-800 hover:bg-slate-50"
          >
            <Heart className="w-4 h-4 text-red-500" />
            Register as Donor
          </Link>
          <button
            type="button"
            onClick={() => {
              setMobileMenuOpen(false);
              openPlatformNotice();
            }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-amber-800 bg-amber-50/70 hover:bg-amber-50"
          >
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Platform Notice
          </button>

          {isAuthenticated ? (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              {user?.role === 'ADMIN' && (
                <Link
                  href="/admin"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-purple-700 bg-purple-50"
                >
                  <ShieldAlert className="w-4 h-4" />
                  Admin Dashboard
                </Link>
              )}
              {user?.role === 'DONOR' && (
                <Link
                  href="/donor/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-red-600 bg-red-50"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Donor Hub
                </Link>
              )}
              {user?.role === 'REQUESTER' && (
                <Link
                  href="/requester/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-red-600 bg-red-50"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  My Requests
                </Link>
              )}
              <div className="px-3.5 py-2.5 flex items-center justify-between text-xs text-slate-700 bg-slate-100 rounded-xl font-medium">
                <div>
                  <div className="font-bold text-slate-900">{user?.name || 'User'}</div>
                  <div className="text-[11px] text-slate-500">{user?.mobile || user?.mobile_number} ({user?.role})</div>
                </div>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="text-red-600 font-bold hover:underline cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            </div>
          ) : (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              <Link
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-3 px-4 text-center font-bold text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-xl flex items-center justify-center gap-2"
              >
                <Heart className="w-4 h-4 text-red-600" />
                <span>Register as Voluntary Donor</span>
              </Link>

              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  openLoginModal();
                }}
                className="w-full py-3 px-4 text-center font-bold text-sm bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-xl shadow-xs cursor-pointer flex items-center justify-center gap-2"
              >
                <MessageCircle className="w-4 h-4" />
                <span>Sign In (WhatsApp / Mobile OTP)</span>
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
