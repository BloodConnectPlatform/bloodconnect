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
  User as UserIcon,
  ShieldCheck,
  Calendar,
  Sparkles,
  MapPin,
  Trash2,
  X,
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

  // Delete Request State
  const [requestToDelete, setRequestToDelete] = useState<BloodRequest | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [reqData, notifData] = await Promise.all([
        api.getMySentRequests(1, 50),
        api.getNotifications(1, 50),
      ]);
      const list = Array.isArray(reqData) ? reqData : (reqData?.items || []);
      setRequests(list);
      setNotifications(notifData?.items || []);
    } catch (err) {
      console.error('Failed to load requester dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRequest = async () => {
    if (!requestToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteRequest(requestToDelete.id);
      setRequests((prev) => prev.filter((r) => r.id !== requestToDelete.id));
      setActionSuccessMessage('Blood request deleted successfully. The target donor has been notified that your requirement was fulfilled.');
      setRequestToDelete(null);
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete blood request. Please try again.');
    } finally {
      setIsDeleting(false);
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
        <p className="text-sm font-medium">Loading your requester dashboard & requests...</p>
      </div>
    );
  }

  const unreadNotifCount = notifications.filter((n) => !n.is_read).length;
  const pendingCount = requests.filter((r) => r.status === 'PENDING').length;
  const acceptedCount = requests.filter((r) => r.status === 'ACCEPTED').length;

  const displayName = user?.name || 'Registered Requester';
  const displayMobile = user?.mobile || user?.mobile_number || '—';

  return (
    <div className="flex-1 bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Action Success Alert Banner */}
        {actionSuccessMessage && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between gap-3 text-xs text-emerald-800 animate-in fade-in">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span className="font-semibold">{actionSuccessMessage}</span>
            </div>
            <button
              onClick={() => setActionSuccessMessage(null)}
              className="text-emerald-700 hover:text-emerald-900 font-bold p-1 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* Requester Identity & Profile Banner */}
        <div className="bg-white rounded-3xl p-6 md:p-8 shadow-xs border border-slate-200/80">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Left: Profile Information */}
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-600 to-rose-700 text-white flex items-center justify-center font-black text-2xl shadow-md shadow-red-500/20 flex-shrink-0">
                <UserIcon className="w-8 h-8" />
              </div>

              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-2xl font-black text-slate-900">{displayName}</h1>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-black uppercase bg-red-100 text-red-800">
                    {user?.role || 'REQUESTER'}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    Verified Mobile
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 font-medium">
                  <span className="flex items-center gap-1 text-slate-700 font-bold">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    {displayMobile}
                  </span>
                  {user?.created_at && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-slate-500">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        Member since {new Date(user.created_at).toLocaleDateString()}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Quick Stats & Search Action */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2.5 px-4 text-center">
                <div>
                  <div className="text-lg font-black text-slate-900">{requests.length}</div>
                  <div className="text-[10px] uppercase font-bold text-slate-500">Total Sent</div>
                </div>
              </div>

              <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-2xl p-2.5 px-4 text-center">
                <div>
                  <div className="text-lg font-black text-amber-900">{pendingCount}</div>
                  <div className="text-[10px] uppercase font-bold text-amber-700">Pending</div>
                </div>
              </div>

              <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-2xl p-2.5 px-4 text-center">
                <div>
                  <div className="text-lg font-black text-emerald-900">{acceptedCount}</div>
                  <div className="text-[10px] uppercase font-bold text-emerald-700">Accepted</div>
                </div>
              </div>

              <Link
                href="/find-donor"
                className="py-3 px-5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-red-500/20 transition-all flex items-center gap-2 cursor-pointer"
              >
                <Search className="w-4 h-4" />
                <span>Search Voluntary Donors</span>
              </Link>
            </div>
          </div>
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
            Sent Blood Requests ({requests.length})
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
                  If you need blood for an emergency patient, search voluntary donors in Tamil Nadu and click <strong>Request Contact</strong>.
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
              requests.map((req) => {
                const reqBloodGroup = req.blood_group || req.donor?.blood_group || 'Blood';
                const donorName = req.donor_name || req.donor?.full_name || req.donor?.name || 'Voluntary Donor';
                const locationName = req.location?.name || req.donor?.location?.name || 'Tamil Nadu';
                const unlockedPhone = req.donor_mobile || req.donor_contact;

                return (
                  <div
                    key={String(req.id)}
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
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="px-3 py-1 rounded-xl text-xs font-black uppercase bg-red-100 text-red-800">
                          {reqBloodGroup} Request
                        </span>

                        {req.status === 'ACCEPTED' && (
                          <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-emerald-100 text-emerald-800 flex items-center gap-1.5">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            Donor Accepted & Phone Unlocked
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

                        <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {locationName}
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-400 font-medium hidden sm:inline">
                          Sent on {new Date(req.created_at).toLocaleDateString()}
                        </span>

                        <button
                          onClick={() => {
                            setRequestToDelete(req);
                            setDeleteError(null);
                          }}
                          className="px-2.5 py-1 text-slate-500 hover:text-red-700 hover:bg-red-50 border border-slate-200 hover:border-red-200 rounded-xl transition-all cursor-pointer flex items-center gap-1 text-xs font-semibold"
                          title="Delete or cancel this blood request"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-red-500" />
                          <span>Delete Request</span>
                        </button>
                      </div>
                    </div>

                    {/* Body Content */}
                    <div className="py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Left: Request & Medical Information */}
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Request Details
                        </div>

                        {req.message ? (
                          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-800 leading-relaxed space-y-1 font-medium">
                            {req.message}
                          </div>
                        ) : (
                          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-600">
                            Urgent requirement for {reqBloodGroup} blood.
                          </div>
                        )}

                        {/* Quick fulfilled note */}
                        <div className="pt-2 text-[11px] text-slate-500 flex items-center gap-1.5">
                          <span>Got requirement satisfied?</span>
                          <button
                            type="button"
                            onClick={() => {
                              setRequestToDelete(req);
                              setDeleteError(null);
                            }}
                            className="text-red-600 hover:underline font-bold cursor-pointer"
                          >
                            Delete / Cancel Request
                          </button>
                        </div>
                      </div>

                      {/* Right: Target Voluntary Donor Details & Unlocked Phone */}
                      <div className="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/80 flex flex-col justify-between">
                        <div>
                          <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                            Target Voluntary Donor
                          </div>
                          <div className="text-base font-bold text-slate-900">
                            {donorName}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            Blood Group: <strong>{reqBloodGroup}</strong> • Location: {locationName}
                          </div>
                        </div>

                        {/* Unlocked Contact Box when ACCEPTED */}
                        {req.status === 'ACCEPTED' && unlockedPhone ? (
                          <div className="mt-4 pt-4 border-t border-emerald-200 space-y-3">
                            <div className="flex items-center gap-2 text-xs font-bold text-emerald-950 bg-emerald-100/70 p-3 rounded-xl border border-emerald-200">
                              <Phone className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                              <span>Verified Donor Contact: {unlockedPhone}</span>
                            </div>

                            <div className="flex items-center gap-2">
                              <a
                                href={`tel:${unlockedPhone}`}
                                className="flex-1 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-xs transition-all"
                              >
                                <Phone className="w-3.5 h-3.5" />
                                Call Donor
                              </a>

                              <a
                                href={`https://wa.me/${unlockedPhone.replace(/\D/g, '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 py-2.5 px-3 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-xs transition-all"
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
                              className="w-full py-2.5 px-3 bg-red-50 hover:bg-red-100 text-red-700 font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                            >
                              <Search className="w-3.5 h-3.5" />
                              Search Other {reqBloodGroup} Donors
                            </Link>
                          </div>
                        ) : (
                          <div className="mt-4 pt-4 border-t border-slate-200 text-xs text-slate-500 flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                            <span>Donor phone number will unlock automatically when they accept.</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
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

      {/* ================= DELETE CONFIRMATION MODAL ================= */}
      {requestToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center">
                <Trash2 className="w-6 h-6" />
              </div>
              <button
                onClick={() => setRequestToDelete(null)}
                disabled={isDeleting}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-900">Delete Blood Request?</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                If your requirement for <strong>{requestToDelete.blood_group || 'Blood'}</strong> blood was fulfilled or is no longer needed, you can delete this request. It will be removed from your dashboard and the target donor will be notified that the requirement was satisfied.
              </p>
            </div>

            {deleteError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs text-red-700">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{deleteError}</span>
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setRequestToDelete(null)}
                disabled={isDeleting}
                className="flex-1 py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer"
              >
                Keep Request
              </button>
              <button
                type="button"
                onClick={handleDeleteRequest}
                disabled={isDeleting}
                className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-md shadow-red-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:bg-slate-300"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Yes, Delete Request</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
