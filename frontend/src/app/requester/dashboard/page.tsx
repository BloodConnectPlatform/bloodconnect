'use client';

import React, { useState, useEffect, useMemo } from 'react';
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
  MapPin,
  Trash2,
  X,
  Copy,
  Check,
  RefreshCw,
  ArrowRight,
  Plus,
  ExternalLink,
  ChevronRight,
  User,
  Calendar,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { BloodRequest, NotificationItem, RequestStatus, UrgencyLevel } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';

export default function RequesterDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [requests, setRequests] = useState<BloodRequest[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'REQUESTS' | 'NOTIFICATIONS'>('REQUESTS');

  // Filter State: 'ALL' | 'ACCEPTED' | 'PENDING' | 'REJECTED'
  const [statusFilter, setStatusFilter] = useState<'ALL' | RequestStatus>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected request for details modal
  const [selectedRequest, setSelectedRequest] = useState<BloodRequest | null>(null);

  // Copy feedback state
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Delete modal state
  const [requestToDelete, setRequestToDelete] = useState<BloodRequest | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchData = async (isManual = false) => {
    if (isManual) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const [reqData, notifData] = await Promise.all([
        api.getMySentRequests(1, 50),
        api.getNotifications(1, 50),
      ]);
      const list = Array.isArray(reqData) ? reqData : (reqData?.items || []);
      setRequests(list);
      setNotifications(notifData?.items || []);
    } catch (err) {
      console.error('Failed to load requests:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const handleCopy = (id: string | number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(String(id));
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDelete = async () => {
    if (!requestToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteRequest(requestToDelete.id);
      setRequests((prev) => prev.filter((r) => r.id !== requestToDelete.id));
      // If currently open in detail modal, close it
      if (selectedRequest?.id === requestToDelete.id) {
        setSelectedRequest(null);
      }
      setToastMessage('Request deleted successfully.');
      setRequestToDelete(null);
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete request.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  // Filter requests
  const filteredRequests = useMemo(() => {
    return requests.filter((req) => {
      if (statusFilter !== 'ALL' && req.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const donor = (req.donor_name || req.donor?.full_name || req.donor?.name || '').toLowerCase();
        const hospital = (req.hospital_name || '').toLowerCase();
        const patient = (req.patient_name || '').toLowerCase();
        const blood = (req.blood_group || req.donor?.blood_group || '').toLowerCase();
        return donor.includes(q) || hospital.includes(q) || patient.includes(q) || blood.includes(q);
      }
      return true;
    });
  }, [requests, statusFilter, searchQuery]);

  const unreadNotifCount = notifications.filter((n) => !n.is_read).length;
  const acceptedCount = requests.filter((r) => r.status === 'ACCEPTED').length;
  const pendingCount = requests.filter((r) => r.status === 'PENDING').length;
  const rejectedCount = requests.filter((r) => r.status === 'REJECTED').length;

  const formatRelativeTime = (dateStr: string) => {
    try {
      const diffMins = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000);
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${Math.floor(diffHours / 24)}d ago`;
    } catch {
      return '';
    }
  };

  const formatFullDateTime = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return dateStr;
    }
  };

  const getUrgencyBadge = (urgency?: UrgencyLevel) => {
    switch (urgency) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase bg-red-100 text-red-800 border border-red-200">
            Critical
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase bg-orange-100 text-orange-800 border border-orange-200">
            High Urgency
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-amber-100 text-amber-800 border border-amber-200">
            Medium
          </span>
        );
      case 'LOW':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            Standard
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            Urgent
          </span>
        );
    }
  };

  if (authLoading || (isLoading && !isRefreshing)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-32 text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <p className="text-sm font-medium text-slate-600">Loading your requests...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-50/60 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 space-y-6">

        {/* Toast Notification */}
        {toastMessage && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-800 font-semibold shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>{toastMessage}</span>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-emerald-700 hover:text-emerald-950 font-bold p-1 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* ================= SIMPLE & ELEGANT HEADER ================= */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              My Requests
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1 font-medium">
              Track responses, view full request details, and connect directly with donors.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchData(true)}
              disabled={isRefreshing}
              className="p-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl transition-all cursor-pointer shadow-2xs"
              title="Refresh status"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-red-600' : ''}`} />
            </button>

            <Link
              href="/find-donor"
              className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Request Donor</span>
            </Link>
          </div>
        </div>

        {/* ================= TABS: REQUESTS vs ALERTS ================= */}
        <div className="flex items-center justify-between border-b border-slate-200 gap-4">
          <div className="flex items-center gap-6">
            <button
              onClick={() => setActiveTab('REQUESTS')}
              className={`pb-3 text-sm font-bold transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
                activeTab === 'REQUESTS'
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <span>Blood Requests</span>
              <span className="px-2 py-0.5 rounded-full text-xs font-black bg-slate-100 text-slate-700">
                {requests.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('NOTIFICATIONS')}
              className={`pb-3 text-sm font-bold transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
                activeTab === 'NOTIFICATIONS'
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <span>Alerts</span>
              {unreadNotifCount > 0 ? (
                <span className="px-2 py-0.5 rounded-full text-xs font-black bg-red-600 text-white">
                  {unreadNotifCount}
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-500">
                  {notifications.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* ================= TAB 1: REQUESTS ================= */}
        {activeTab === 'REQUESTS' && (
          <div className="space-y-4">
            
            {/* Filter Pills */}
            {requests.length > 0 && (
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => setStatusFilter('ALL')}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                      statusFilter === 'ALL'
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                    }`}
                  >
                    All ({requests.length})
                  </button>

                  <button
                    onClick={() => setStatusFilter('ACCEPTED')}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                      statusFilter === 'ACCEPTED'
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-white text-emerald-800 hover:bg-emerald-50 border border-emerald-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${statusFilter === 'ACCEPTED' ? 'bg-white' : 'bg-emerald-500'}`} />
                    <span>Accepted ({acceptedCount})</span>
                  </button>

                  <button
                    onClick={() => setStatusFilter('PENDING')}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                      statusFilter === 'PENDING'
                        ? 'bg-amber-500 text-white shadow-xs'
                        : 'bg-white text-amber-800 hover:bg-amber-50 border border-amber-200'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${statusFilter === 'PENDING' ? 'bg-white' : 'bg-amber-500'}`} />
                    <span>Waiting ({pendingCount})</span>
                  </button>

                  {rejectedCount > 0 && (
                    <button
                      onClick={() => setStatusFilter('REJECTED')}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        statusFilter === 'REJECTED'
                          ? 'bg-slate-700 text-white shadow-xs'
                          : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                      }`}
                    >
                      Declined ({rejectedCount})
                    </button>
                  )}
                </div>

                {/* Optional Search */}
                {requests.length > 2 && (
                  <div className="relative w-full sm:w-56">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Search donor or hospital..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Zero Requests State */}
            {requests.length === 0 ? (
              <div className="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-xs space-y-4">
                <div className="w-12 h-12 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto">
                  <Droplet className="w-6 h-6 fill-red-600" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-black text-slate-900">No requests sent yet</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Search registered blood donors in Tamil Nadu and send a request when blood is needed.
                  </p>
                </div>
                <Link
                  href="/find-donor"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-xs transition-all"
                >
                  <Search className="w-4 h-4" />
                  <span>Find a Donor</span>
                </Link>
              </div>
            ) : filteredRequests.length === 0 ? (
              <div className="bg-white rounded-2xl p-8 text-center border border-slate-200 text-xs text-slate-500 space-y-2">
                <p className="font-semibold text-slate-700">No requests matching this filter.</p>
                <button
                  onClick={() => { setStatusFilter('ALL'); setSearchQuery(''); }}
                  className="text-red-600 font-bold hover:underline"
                >
                  Show all requests
                </button>
              </div>
            ) : (
              /* Request Cards */
              <div className="space-y-4">
                {filteredRequests.map((req) => {
                  const reqBloodGroup = req.blood_group || req.donor?.blood_group || 'Blood';
                  const donorName = req.donor_name || req.donor?.full_name || req.donor?.name || 'Voluntary Donor';
                  const locationName = req.location?.name || req.donor?.location?.name || 'Tamil Nadu';
                  const phone = req.donor_mobile || req.donor_contact;
                  const isAccepted = req.status === 'ACCEPTED';
                  const isPending = req.status === 'PENDING';
                  const isDeclined = req.status === 'REJECTED';
                  const timeAgo = formatRelativeTime(req.created_at);

                  return (
                    <div
                      key={String(req.id)}
                      onClick={() => setSelectedRequest(req)}
                      className={`bg-white rounded-2xl p-5 sm:p-6 border transition-all cursor-pointer hover:shadow-md ${
                        isAccepted
                          ? 'border-emerald-300 shadow-xs ring-1 ring-emerald-400/20 hover:border-emerald-400'
                          : isPending
                          ? 'border-amber-200 shadow-2xs hover:border-amber-300'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      {/* Card Header: Donor, Status & Prominent Delete */}
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                        <div className="flex items-center gap-3">
                          <div className="w-11 h-11 rounded-xl bg-red-600 text-white flex items-center justify-center font-black text-sm shadow-2xs flex-shrink-0">
                            {reqBloodGroup}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="text-base font-black text-slate-900 leading-tight">
                                {donorName}
                              </h3>
                              <span className="text-[11px] text-slate-400 font-medium hidden sm:inline">
                                (Click for details)
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium mt-0.5">
                              <MapPin className="w-3 h-3 text-slate-400" />
                              <span>{locationName}</span>
                              {timeAgo && <span>&bull; {timeAgo}</span>}
                            </div>
                          </div>
                        </div>

                        {/* Status Badge & Prominent Delete Button */}
                        <div className="flex items-center gap-2 self-start sm:self-auto">
                          {isAccepted && (
                            <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-emerald-100 text-emerald-800 flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Accepted</span>
                            </span>
                          )}
                          {isPending && (
                            <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-amber-100 text-amber-800 flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5 text-amber-600 animate-spin" />
                              <span>Waiting</span>
                            </span>
                          )}
                          {isDeclined && (
                            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-slate-100 text-slate-600 flex items-center gap-1">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Unavailable</span>
                            </span>
                          )}

                          {/* PROMINENT DELETE BUTTON */}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setRequestToDelete(req);
                              setDeleteError(null);
                            }}
                            className="px-2.5 py-1 text-xs font-bold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl flex items-center gap-1 transition-all cursor-pointer"
                            title="Delete this request"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-600" />
                            <span>Delete</span>
                          </button>
                        </div>
                      </div>

                      {/* Card Body: Hospital, Patient, Urgency */}
                      <div className="py-3 text-xs text-slate-700 flex flex-wrap items-center justify-between gap-2 font-medium">
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                          {req.hospital_name && (
                            <div className="flex items-center gap-1.5">
                              <Building className="w-3.5 h-3.5 text-slate-400" />
                              <span className="font-bold text-slate-900">{req.hospital_name}</span>
                            </div>
                          )}
                          {req.patient_name && (
                            <div>
                              Patient: <span className="font-bold text-slate-900">{req.patient_name}</span>
                            </div>
                          )}
                          {req.required_units && (
                            <div>
                              Units: <span className="font-bold text-slate-900">{req.required_units} Unit(s)</span>
                            </div>
                          )}
                        </div>

                        {/* View Full Info trigger hint */}
                        <div className="flex items-center gap-1 text-[11px] font-bold text-red-600 hover:text-red-700">
                          <span>View full details</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </div>
                      </div>

                      {/* Main Action Box */}
                      <div className="mt-1 pt-3 border-t border-slate-100">
                        {isAccepted && phone ? (
                          /* ACCEPTED: HERO CONTACT BUTTONS */
                          <div
                            onClick={(e) => e.stopPropagation()}
                            className="bg-emerald-50/90 rounded-xl p-3.5 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                          >
                            <div className="space-y-0.5">
                              <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                                Donor Phone Number
                              </div>
                              <div className="text-base font-black text-emerald-950 tracking-wide flex items-center gap-2">
                                <span>{phone}</span>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleCopy(req.id, phone);
                                  }}
                                  className="text-xs text-emerald-700 hover:text-emerald-900 font-bold p-1 cursor-pointer"
                                  title="Copy phone number"
                                >
                                  {copiedId === String(req.id) ? (
                                    <span className="text-[11px] text-emerald-700 font-bold flex items-center gap-0.5">
                                      <Check className="w-3 h-3" /> Copied
                                    </span>
                                  ) : (
                                    <Copy className="w-3.5 h-3.5" />
                                  )}
                                </button>
                              </div>
                            </div>

                            {/* Direct Call & WhatsApp Buttons */}
                            <div className="flex items-center gap-2">
                              <a
                                href={`tel:${phone}`}
                                onClick={(e) => e.stopPropagation()}
                                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 shadow-xs transition-all cursor-pointer"
                              >
                                <Phone className="w-3.5 h-3.5" />
                                <span>Call Donor</span>
                              </a>

                              <a
                                href={`https://wa.me/${phone.replace(/\D/g, '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="px-4 py-2.5 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl flex items-center gap-1.5 shadow-xs transition-all cursor-pointer"
                              >
                                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                                <span>WhatsApp</span>
                              </a>
                            </div>
                          </div>
                        ) : isPending ? (
                          /* PENDING: SIMPLE STATUS & ACTION */
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                            <span className="text-slate-500 font-medium">
                              Waiting for donor to accept. Contact details will unlock immediately upon acceptance.
                            </span>
                            <Link
                              href={`/find-donor?blood_group=${encodeURIComponent(reqBloodGroup)}`}
                              onClick={(e) => e.stopPropagation()}
                              className="text-red-600 hover:underline font-bold whitespace-nowrap flex items-center gap-1"
                            >
                              <span>Find another donor</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        ) : (
                          /* DECLINED */
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                            <span className="text-slate-500 font-medium">
                              Donor is currently unavailable.
                            </span>
                            <Link
                              href={`/find-donor?blood_group=${encodeURIComponent(reqBloodGroup)}`}
                              onClick={(e) => e.stopPropagation()}
                              className="text-red-600 hover:underline font-bold whitespace-nowrap flex items-center gap-1"
                            >
                              <span>Request other {reqBloodGroup} donors</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 2: ALERTS & NOTIFICATIONS ================= */}
        {activeTab === 'NOTIFICATIONS' && (
          <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Notifications</h3>
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
              <div className="py-12 text-center text-xs text-slate-400">
                No notifications yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`py-3.5 flex items-start gap-3 rounded-xl px-2 ${
                      !notif.is_read ? 'bg-red-50/40' : ''
                    }`}
                  >
                    <div className="p-2 bg-red-100 text-red-600 rounded-xl flex-shrink-0 mt-0.5">
                      <Bell className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-900">{notif.title}</span>
                        <span className="text-[10px] text-slate-400">{formatRelativeTime(notif.created_at)}</span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{notif.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Medical Notice */}
        <MedicalDisclaimer variant="card" />
      </div>

      {/* ================= DETAILED INFO MODAL ================= */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto animate-in fade-in">
          <div className="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden my-8 max-h-[90vh] flex flex-col">
            
            {/* Modal Header */}
            <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center font-black text-sm text-white shadow-xs">
                  {selectedRequest.blood_group || selectedRequest.donor?.blood_group || 'Blood'}
                </div>
                <div>
                  <h2 className="text-base font-black text-white leading-tight">Request Details</h2>
                  <p className="text-xs text-slate-300">
                    ID #{String(selectedRequest.id)} &bull; {formatRelativeTime(selectedRequest.created_at)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedRequest(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 space-y-5 overflow-y-auto flex-1 text-slate-800">
              
              {/* Status & Urgency Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-slate-50 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500">Status:</span>
                  {selectedRequest.status === 'ACCEPTED' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-black uppercase bg-emerald-100 text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Accepted</span>
                    </span>
                  )}
                  {selectedRequest.status === 'PENDING' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-black uppercase bg-amber-100 text-amber-800 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-amber-600 animate-spin" />
                      <span>Awaiting Response</span>
                    </span>
                  )}
                  {selectedRequest.status === 'REJECTED' && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-slate-200 text-slate-700 flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Unavailable / Declined</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500">Urgency:</span>
                  {getUrgencyBadge(selectedRequest.urgency)}
                </div>
              </div>

              {/* Donor Contact Card (If accepted) */}
              {selectedRequest.status === 'ACCEPTED' && (selectedRequest.donor_mobile || selectedRequest.donor_contact) ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-emerald-800 uppercase tracking-wider">
                      Donor Direct Contact
                    </span>
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                      Verified
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-lg font-black text-emerald-950">
                        {selectedRequest.donor_mobile || selectedRequest.donor_contact}
                      </div>
                      <div className="text-xs font-semibold text-emerald-700">
                        {selectedRequest.donor_name || selectedRequest.donor?.full_name || 'Donor'}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleCopy(selectedRequest.id, (selectedRequest.donor_mobile || selectedRequest.donor_contact)!)}
                      className="px-2.5 py-1.5 bg-white hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-1 cursor-pointer transition-colors shadow-2xs"
                    >
                      {copiedId === String(selectedRequest.id) ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <a
                      href={`tel:${selectedRequest.donor_mobile || selectedRequest.donor_contact}`}
                      className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
                    >
                      <Phone className="w-4 h-4" />
                      <span>Call Donor</span>
                    </a>

                    <a
                      href={`https://wa.me/${(selectedRequest.donor_mobile || selectedRequest.donor_contact || '').replace(/\D/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2.5 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
                    >
                      <MessageSquare className="w-4 h-4 text-emerald-400" />
                      <span>WhatsApp</span>
                    </a>
                  </div>
                </div>
              ) : selectedRequest.status === 'PENDING' ? (
                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-900 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-950">
                    <Clock className="w-4 h-4 text-amber-600" />
                    <span>Awaiting Donor Acceptance</span>
                  </div>
                  <p className="text-amber-800 leading-relaxed font-medium">
                    The donor has received an alert for this request. Once they accept, their direct contact number will appear right here and in your alerts.
                  </p>
                </div>
              ) : (
                <div className="bg-slate-100 border border-slate-200 rounded-2xl p-4 text-xs text-slate-700 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-slate-900">
                    <XCircle className="w-4 h-4 text-slate-600" />
                    <span>Donor Unavailable</span>
                  </div>
                  <p className="text-slate-600 leading-relaxed font-medium">
                    This donor was unable to fulfill this request. You can search for other matching voluntary donors in the same district.
                  </p>
                </div>
              )}

              {/* Detailed Breakdown Grid */}
              <div className="space-y-3">
                <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider">
                  Request Information
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  
                  {/* Donor */}
                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
                    <span className="text-[11px] text-slate-500 font-bold">Target Donor</span>
                    <div className="font-black text-slate-900 text-sm">
                      {selectedRequest.donor_name || selectedRequest.donor?.full_name || selectedRequest.donor?.name || 'Voluntary Donor'}
                    </div>
                    <div className="text-slate-600 font-medium flex items-center gap-1 text-[11px]">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      <span>{selectedRequest.location?.name || selectedRequest.donor?.location?.name || 'Tamil Nadu'}</span>
                    </div>
                  </div>

                  {/* Patient */}
                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
                    <span className="text-[11px] text-slate-500 font-bold">Patient Name</span>
                    <div className="font-black text-slate-900 text-sm">
                      {selectedRequest.patient_name || 'Not specified'}
                    </div>
                    <div className="text-slate-600 font-medium text-[11px]">
                      Units Required: <strong className="text-slate-900">{selectedRequest.required_units || 1} Unit(s)</strong>
                    </div>
                  </div>

                  {/* Hospital */}
                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1 sm:col-span-2">
                    <span className="text-[11px] text-slate-500 font-bold">Hospital / Medical Center</span>
                    <div className="font-black text-slate-900 text-sm flex items-center gap-1.5">
                      <Building className="w-4 h-4 text-slate-400" />
                      <span>{selectedRequest.hospital_name || 'Hospital name not specified'}</span>
                    </div>
                  </div>

                  {/* Timestamps */}
                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
                    <span className="text-[11px] text-slate-500 font-bold">Sent On</span>
                    <div className="font-bold text-slate-900 text-xs">
                      {formatFullDateTime(selectedRequest.created_at)}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
                    <span className="text-[11px] text-slate-500 font-bold">Response Updated</span>
                    <div className="font-bold text-slate-900 text-xs">
                      {selectedRequest.responded_at || selectedRequest.updated_at
                        ? formatFullDateTime(selectedRequest.responded_at || selectedRequest.updated_at)
                        : 'Pending Response'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Message / Requirement Note */}
              {selectedRequest.message && (
                <div className="space-y-1.5">
                  <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider">
                    Additional Notes / Message
                  </h3>
                  <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-xs text-slate-700 leading-relaxed font-medium">
                    {selectedRequest.message}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer Actions */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => {
                  setRequestToDelete(selectedRequest);
                  setDeleteError(null);
                }}
                className="px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 hover:text-red-700 border border-red-200 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Request</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedRequest(null)}
                className="px-5 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= REMOVE CONFIRMATION MODAL ================= */}
      {requestToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-sm bg-white rounded-3xl shadow-2xl border border-slate-100 p-6 space-y-4">
            <div className="w-11 h-11 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center">
              <Trash2 className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-black text-slate-900">Delete Blood Request?</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-medium">
                Are you sure you want to delete this request for <strong>{requestToDelete.blood_group || 'Blood'}</strong> sent to{' '}
                <strong>{requestToDelete.donor_name || requestToDelete.donor?.full_name || 'Donor'}</strong>? This action cannot be undone.
              </p>
            </div>

            {deleteError && (
              <div className="p-2.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-semibold">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRequestToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2.5 text-xs font-bold text-slate-600 hover:text-slate-800 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-xs disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Yes, Delete</span>
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
