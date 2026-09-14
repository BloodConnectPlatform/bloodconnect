'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Search,
  Droplet,
  Clock,
  CheckCircle2,
  XCircle,
  Phone,
  MessageSquare,
  AlertCircle,
  Bell,
  Loader2,
  Building,
  Heart,
  ExternalLink,
} from 'lucide-react';
import { BloodRequest, NotificationItem } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';

export default function RequesterDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [requests, setRequests] = useState<BloodRequest[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'REQUESTS' | 'NOTIFICATIONS'>('REQUESTS');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [reqData, notifData] = await Promise.all([
        api.getMySentRequests(1, 20),
        api.getNotifications(1, 20),
      ]);
      setRequests(reqData.items);
      setNotifications(notifData.items);
    } catch {
      // Handled
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <p className="text-sm font-medium">Loading your blood requests...</p>
      </div>
    );
  }

  const unreadNotifCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="flex-1 bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 rounded-lg text-xs font-bold text-red-800 mb-2">
              <Clock className="w-3.5 h-3.5" />
              <span>Requester Status Center</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900">
              My Sent Blood Requests
            </h1>
            <p className="text-xs sm:text-sm text-slate-600">
              Track your emergency requests. When a voluntary donor accepts, their phone number is immediately revealed.
            </p>
          </div>

          <Link
            href="/find-donor"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl shadow-md shadow-red-500/20 transition-all cursor-pointer"
          >
            <Search className="w-4 h-4" />
            <span>Search More Donors</span>
          </Link>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('REQUESTS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'REQUESTS'
                ? 'bg-red-600 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Droplet className="w-3.5 h-3.5" />
            Sent Requests ({requests.length})
          </button>

          <button
            onClick={() => setActiveTab('NOTIFICATIONS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'NOTIFICATIONS'
                ? 'bg-red-600 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            Notifications
            {unreadNotifCount > 0 && (
              <span className="px-1.5 py-0.2 bg-red-600 text-white rounded-full text-[10px] font-black">
                {unreadNotifCount}
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: REQUESTS LIST */}
        {activeTab === 'REQUESTS' && (
          <div className="space-y-6">
            {requests.length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 space-y-4">
                <div className="w-12 h-12 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto">
                  <Search className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-slate-800">No Blood Requests Sent Yet</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  If you need blood for a patient, search for matching voluntary donors in Tamil Nadu and send an emergency request.
                </p>
                <Link
                  href="/find-donor"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white font-bold text-xs rounded-xl shadow-xs"
                >
                  <Search className="w-4 h-4" />
                  Find Donors Now
                </Link>
              </div>
            ) : (
              requests.map((req) => (
                <div
                  key={req.id}
                  className={`bg-white rounded-3xl p-6 md:p-8 border shadow-xs transition-all ${
                    req.status === 'ACCEPTED'
                      ? 'border-emerald-300 ring-2 ring-emerald-500/20'
                      : req.status === 'REJECTED'
                      ? 'border-slate-200 opacity-90'
                      : 'border-amber-200'
                  }`}
                >
                  {/* Status Banner */}
                  <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
                    <div className="flex items-center gap-2.5">
                      {req.status === 'ACCEPTED' && (
                        <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-emerald-100 text-emerald-800 flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          Donor Accepted & Unlocked
                        </span>
                      )}
                      {req.status === 'PENDING' && (
                        <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-amber-100 text-amber-800 flex items-center gap-1.5">
                          <Clock className="w-4 h-4 text-amber-600 animate-spin" />
                          Awaiting Donor Response
                        </span>
                      )}
                      {req.status === 'REJECTED' && (
                        <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-slate-100 text-slate-600 flex items-center gap-1.5">
                          <XCircle className="w-4 h-4 text-slate-400" />
                          Donor Unavailable / Declined
                        </span>
                      )}

                      <span className="text-xs text-slate-400 font-medium">
                        Sent {new Date(req.created_at).toLocaleString()}
                      </span>
                    </div>

                    <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700">
                      {req.urgency} Urgency
                    </span>
                  </div>

                  {/* Body Content */}
                  <div className="py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left: Patient & Hospital */}
                    <div className="space-y-3">
                      <h3 className="text-lg font-bold text-slate-900">
                        Patient: {req.patient_name} ({req.required_units} Unit(s))
                      </h3>
                      <div className="text-xs text-slate-600 space-y-1">
                        <div className="flex items-center gap-1.5 font-medium">
                          <Building className="w-3.5 h-3.5 text-slate-400" />
                          <span>Hospital: {req.hospital_name}</span>
                        </div>
                        {req.message && (
                          <div className="p-3 bg-slate-50 rounded-xl text-slate-600 italic">
                            "{req.message}"
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right: Donor Details & Phone Disclosure */}
                    <div className="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/80 flex flex-col justify-between">
                      <div>
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                          Requested Voluntary Donor
                        </div>
                        <div className="text-base font-bold text-slate-900">
                          {req.donor?.full_name || 'Registered Donor'}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Blood Group: <strong>{req.donor?.blood_group}</strong> • Location:{' '}
                          {req.donor?.location?.taluk}, {req.donor?.location?.district}
                        </div>
                      </div>

                      {/* Unlocked Contact Box when ACCEPTED */}
                      {req.status === 'ACCEPTED' && req.donor_contact ? (
                        <div className="mt-4 pt-4 border-t border-emerald-200 space-y-3">
                          <div className="flex items-center gap-2 text-xs font-bold text-emerald-900 bg-emerald-100/60 p-2.5 rounded-xl border border-emerald-200">
                            <Phone className="w-4 h-4 text-emerald-600" />
                            <span>Verified Donor Mobile: {req.donor_contact}</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <a
                              href={`tel:${req.donor_contact}`}
                              className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-xs transition-all"
                            >
                              <Phone className="w-3.5 h-3.5" />
                              Call Donor Directly
                            </a>

                            <a
                              href={`https://wa.me/${req.donor_contact.replace(/\D/g, '')}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-1 py-2 px-3 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-xs transition-all"
                            >
                              <MessageSquare className="w-3.5 h-3.5" />
                              WhatsApp
                            </a>
                          </div>
                        </div>
                      ) : req.status === 'REJECTED' ? (
                        <div className="mt-4 pt-4 border-t border-slate-200">
                          <Link
                            href="/find-donor"
                            className="w-full py-2 px-3 bg-red-50 hover:bg-red-100 text-red-700 font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                          >
                            <Search className="w-3.5 h-3.5" />
                            Search Other {req.donor?.blood_group} Donors
                          </Link>
                        </div>
                      ) : (
                        <div className="mt-4 pt-4 border-t border-slate-200 text-xs text-slate-500 flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-amber-500" />
                          <span>Donor phone will unlock as soon as they accept.</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 2: NOTIFICATIONS LIST */}
        {activeTab === 'NOTIFICATIONS' && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">In-App Notifications</h3>
              {unreadNotifCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-xs font-bold text-red-600 hover:underline cursor-pointer"
                >
                  Mark all as read
                </button>
              )}
            </div>

            {notifications.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">
                No notifications received yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`py-3.5 flex items-start gap-3 ${
                      !notif.is_read ? 'bg-red-50/40 px-3 rounded-xl' : ''
                    }`}
                  >
                    <div className="p-2 bg-red-100 rounded-xl text-red-600 flex-shrink-0 mt-0.5">
                      <Bell className="w-4 h-4" />
                    </div>
                    <div className="flex-1 space-y-0.5">
                      <div className="text-xs font-bold text-slate-900">{notif.title}</div>
                      <p className="text-xs text-slate-600">{notif.message}</p>
                      <div className="text-[10px] text-slate-400">
                        {new Date(notif.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Safety Disclaimer */}
        <MedicalDisclaimer variant="card" />
      </div>
    </div>
  );
}
