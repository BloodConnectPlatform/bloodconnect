'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import {
  Heart,
  Droplet,
  Search,
  UserPlus,
  LayoutDashboard,
  Bell,
  LogOut,
  ShieldAlert,
  Menu,
  X,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, donorProfile, isAuthenticated, openLoginModal, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
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
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center text-white shadow-md shadow-red-500/20 group-hover:scale-105 transition-transform">
              <Droplet className="w-6 h-6 fill-white text-white" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-slate-900 flex items-center gap-1">
                Blood<span className="text-red-600">Connect</span>
              </span>
              <span className="block text-[10px] font-semibold text-slate-400 -mt-1 tracking-wider uppercase">
                Tamil Nadu Network
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-1.5">
            <Link
              href="/"
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${
                pathname === '/'
                  ? 'text-red-600 bg-red-50/80'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              Home
            </Link>

            <Link
              href="/#about-initiative"
              className="px-3 py-2 rounded-lg text-sm font-semibold text-slate-700 hover:text-red-600 hover:bg-slate-50 transition-colors"
            >
              About Our Initiative
            </Link>

            <Link
              href="/register"
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                pathname === '/register'
                  ? 'text-red-600 bg-red-50/80'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              <Heart className="w-4 h-4 text-red-500" />
              Register as Donor
            </Link>

            <Link
              href="/find-donor"
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                pathname === '/find-donor'
                  ? 'text-red-600 bg-red-50/80'
                  : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
              }`}
            >
              <Search className="w-4 h-4" />
              Find a Donor
            </Link>

            <Link
              href="/#important-note"
              className="px-3 py-2 rounded-lg text-sm font-semibold text-amber-700 hover:text-amber-800 hover:bg-amber-50/80 transition-colors flex items-center gap-1"
            >
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              Important Note
            </Link>

            {isAuthenticated && user?.role === 'ADMIN' && (
              <Link
                href="/admin"
                className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/admin')
                    ? 'text-purple-700 bg-purple-50'
                    : 'text-purple-600 hover:text-purple-700 hover:bg-purple-50/60'
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                Admin Panel
              </Link>
            )}

            {isAuthenticated && user?.role === 'DONOR' && (
              <Link
                href="/donor/dashboard"
                className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/donor')
                    ? 'text-red-600 bg-red-50'
                    : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                Donor Hub
                {donorProfile?.is_available && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="Available for requests" />
                )}
              </Link>
            )}

            {isAuthenticated && user?.role === 'REQUESTER' && (
              <Link
                href="/requester/dashboard"
                className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                  pathname.startsWith('/requester')
                    ? 'text-red-600 bg-red-50'
                    : 'text-slate-700 hover:text-red-600 hover:bg-slate-50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                My Requests
              </Link>
            )}
          </nav>

          {/* Desktop Right Action Area */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-xl text-xs font-semibold text-slate-700 border border-slate-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>{user?.mobile_number}</span>
                  <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-200 text-slate-600">
                    {user?.role}
                  </span>
                </div>

                <button
                  onClick={logout}
                  className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={openLoginModal}
                  className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-red-600 transition-colors cursor-pointer"
                >
                  Sign In
                </button>
                <Link
                  href="/register"
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white text-sm font-semibold rounded-xl shadow-xs shadow-red-500/20 hover:shadow-md transition-all flex items-center gap-1.5"
                >
                  <UserPlus className="w-4 h-4" />
                  Donate Blood
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-700 hover:text-red-600 rounded-lg hover:bg-slate-100 transition-colors"
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
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-slate-800 hover:bg-slate-50"
          >
            Home
          </Link>
          <Link
            href="/#about-initiative"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-slate-800 hover:bg-slate-50"
          >
            About Our Initiative
          </Link>
          <Link
            href="/register"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-slate-800 hover:bg-slate-50"
          >
            <Heart className="w-5 h-5 text-red-500" />
            Register as Donor
          </Link>
          <Link
            href="/find-donor"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-slate-800 hover:bg-slate-50"
          >
            <Search className="w-5 h-5 text-red-600" />
            Find a Donor
          </Link>
          <Link
            href="/#important-note"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-amber-800 bg-amber-50/60 hover:bg-amber-50"
          >
            <AlertCircle className="w-5 h-5 text-amber-600" />
            Important Note
          </Link>

          {isAuthenticated ? (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              {user?.role === 'ADMIN' && (
                <Link
                  href="/admin"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-purple-700 bg-purple-50"
                >
                  <ShieldAlert className="w-5 h-5" />
                  Admin Dashboard
                </Link>
              )}
              {user?.role === 'DONOR' && (
                <Link
                  href="/donor/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-red-600 bg-red-50"
                >
                  <LayoutDashboard className="w-5 h-5" />
                  Donor Hub
                </Link>
              )}
              {user?.role === 'REQUESTER' && (
                <Link
                  href="/requester/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-base font-semibold text-red-600 bg-red-50"
                >
                  <LayoutDashboard className="w-5 h-5" />
                  My Sent Requests
                </Link>
              )}
              <div className="px-3 py-2 flex items-center justify-between text-xs text-slate-600">
                <span>{user?.mobile_number}</span>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="text-red-600 font-semibold"
                >
                  Sign Out
                </button>
              </div>
            </div>
          ) : (
            <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  openLoginModal();
                }}
                className="w-full py-2.5 px-4 text-center font-semibold text-sm border border-slate-300 rounded-xl text-slate-700"
              >
                Sign In
              </button>
              <Link
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-2.5 px-4 text-center font-semibold text-sm bg-red-600 text-white rounded-xl shadow-xs"
              >
                Donate Blood
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
