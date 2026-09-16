'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  ShieldAlert,
  Users,
  Heart,
  Droplet,
  Flag,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Search,
  Filter,
  Trash2,
  Power,
  Loader2,
  FileText,
  Clock,
  MapPin,
  Building,
} from 'lucide-react';
import {
  AdminStats,
  BloodGroup,
  BloodRequest,
  DonorProfile,
  LocationItem,
  ReportItem,
  ReportStatus,
} from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, login, openLoginModal } = useAuth();

  const [activeTab, setActiveTab] = useState<'DONORS' | 'REQUESTS' | 'REPORTS' | 'AUDIT'>('DONORS');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [locations, setLocations] = useState<LocationItem[]>([]);

  // Admin Direct Login State
  const [adminPhone, setAdminPhone] = useState('9876543210');
  const [adminOtp, setAdminOtp] = useState('');
  const [adminLoginStep, setAdminLoginStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [isAdminLoggingIn, setIsAdminLoggingIn] = useState(false);
  const [adminLoginError, setAdminLoginError] = useState<string | null>(null);
  const [adminCooldown, setAdminCooldown] = useState(0);

  // Donors Tab State
  const [donors, setDonors] = useState<DonorProfile[]>([]);
  const [donorSearch, setDonorSearch] = useState('');
  const [donorFilterGroup, setDonorFilterGroup] = useState<string>('');
  const [donorFilterLocation, setDonorFilterLocation] = useState<string>('');
  const [isDonorsLoading, setIsDonorsLoading] = useState(false);

  // Requests Tab State
  const [requests, setRequests] = useState<BloodRequest[]>([]);
  const [isRequestsLoading, setIsRequestsLoading] = useState(false);

  // Reports Tab State
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [isReportsLoading, setIsReportsLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [reportActionStatus, setReportActionStatus] = useState<ReportStatus>('RESOLVED');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isHandlingReport, setIsHandlingReport] = useState(false);

  // Delete Donor Modal
  const [deleteDonorTarget, setDeleteDonorTarget] = useState<DonorProfile | null>(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [isDeletingDonor, setIsDeletingDonor] = useState(false);

  // Audit Logs Tab State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [isAuditLoading, setIsAuditLoading] = useState(false);

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Cooldown timer
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (adminCooldown > 0) {
      timer = setTimeout(() => setAdminCooldown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [adminCooldown]);

  // Load initial data
  const loadStats = async () => {
    try {
      const s = await api.getAdminStats();
      setStats(s);
    } catch {}
  };

  const loadDonors = async () => {
    setIsDonorsLoading(true);
    try {
      const res = await api.listAdminDonors({
        search: donorSearch || undefined,
        blood_group: (donorFilterGroup as BloodGroup) || undefined,
        location_id: donorFilterLocation ? parseInt(donorFilterLocation) : undefined,
      });
      setDonors(res.items);
    } catch {} finally {
      setIsDonorsLoading(false);
    }
  };

  const loadRequests = async () => {
    setIsRequestsLoading(true);
    try {
      const res = await api.listAdminRequests(1, 50);
      setRequests(res.items);
    } catch {} finally {
      setIsRequestsLoading(false);
    }
  };

  const loadReports = async () => {
    setIsReportsLoading(true);
    try {
      const res = await api.listAdminReports();
      setReports(res.items);
    } catch {} finally {
      setIsReportsLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    setIsAuditLoading(true);
    try {
      const res = await api.getAdminAuditLogs();
      setAuditLogs(res.items);
    } catch {} finally {
      setIsAuditLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user?.role === 'ADMIN') {
      loadStats();
      api.getLocations().then(setLocations).catch(() => {});
      loadDonors();
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    if (activeTab === 'DONORS') loadDonors();
    if (activeTab === 'REQUESTS') loadRequests();
    if (activeTab === 'REPORTS') loadReports();
    if (activeTab === 'AUDIT') loadAuditLogs();
  }, [activeTab]);

  const normalizePhone = (num: string) => {
    const cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return `+91${cleaned}`;
    if (cleaned.length === 12 && cleaned.startsWith('91')) return `+${cleaned}`;
    if (num.startsWith('+91') && cleaned.length === 12) return num;
    return `+91${cleaned}`;
  };

  // Direct Admin Login handlers
  const handleSendAdminOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdminLoginError(null);

    const formatted = normalizePhone(adminPhone);
    if (!/^\+91[6-9]\d{9}$/.test(formatted)) {
      setAdminLoginError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setIsAdminLoggingIn(true);
    try {
      const res = await api.sendOtp(formatted, 'LOGIN');
      setAdminLoginStep('OTP');
      setAdminCooldown(res.cooldown_seconds || 60);
      if (res.debug_otp) {
        setAdminOtp(res.debug_otp);
      }
    } catch (err: any) {
      setAdminLoginError(err.message || 'Failed to send OTP.');
    } finally {
      setIsAdminLoggingIn(false);
    }
  };

  const handleVerifyAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdminLoginError(null);

    if (adminOtp.trim().length !== 6) {
      setAdminLoginError('Please enter a valid 6-digit OTP code');
      return;
    }

    setIsAdminLoggingIn(true);
    try {
      const formatted = normalizePhone(adminPhone);
      const loggedUser = await login(formatted, adminOtp.trim());
      if (loggedUser.role !== 'ADMIN') {
        setAdminLoginError(`Account signed in with role '${loggedUser.role}'. Administrator privileges required.`);
      }
    } catch (err: any) {
      setAdminLoginError(err.message || 'Invalid or expired OTP code.');
    } finally {
      setIsAdminLoggingIn(false);
    }
  };

  // Handle donor status toggle
  const handleToggleDonorStatus = async (donor: DonorProfile) => {
    try {
      const newStatus = !(donor.user?.is_active ?? true);
      await api.toggleDonorStatus(donor.id, newStatus, 'Admin moderation action');
      setNotification({
        type: 'success',
        text: `Donor account ${newStatus ? 'activated' : 'deactivated'} successfully.`,
      });
      loadDonors();
      loadStats();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to update donor status.' });
    }
  };

  // Handle donor availability toggle
  const handleToggleDonorAvailability = async (donor: DonorProfile) => {
    try {
      const newAvail = !donor.is_available;
      await api.toggleDonorAvailabilityAdmin(donor.id, newAvail, 'Admin availability override');
      setNotification({
        type: 'success',
        text: `Donor availability updated to ${newAvail ? 'Available' : 'Unavailable'}.`,
      });
      loadDonors();
      loadStats();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to update availability.' });
    }
  };

  // Handle donor deletion
  const handleDeleteDonor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deleteDonorTarget || !deleteReason.trim()) return;

    setIsDeletingDonor(true);
    try {
      await api.deleteDonorAdmin(deleteDonorTarget.id, deleteReason.trim());
      setNotification({ type: 'success', text: 'Donor record deleted successfully.' });
      setDeleteDonorTarget(null);
      setDeleteReason('');
      loadDonors();
      loadStats();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to delete donor.' });
    } finally {
      setIsDeletingDonor(false);
    }
  };

  // Handle report resolution
  const handleResolveReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;

    setIsHandlingReport(true);
    try {
      await api.handleAdminReport(selectedReport.id, reportActionStatus, resolutionNotes || undefined);
      setNotification({ type: 'success', text: `Report marked as ${reportActionStatus}.` });
      setSelectedReport(null);
      setResolutionNotes('');
      loadReports();
      loadStats();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to update report.' });
    } finally {
      setIsHandlingReport(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <p className="text-sm font-medium">Verifying admin credentials...</p>
      </div>
    );
  }

  if (!isAuthenticated || user?.role !== 'ADMIN') {
    return (
      <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-800 to-indigo-900 p-8 text-white text-center relative">
            <div className="w-14 h-14 bg-white/15 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-xs">
              <ShieldAlert className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-black">Admin Operations Center</h2>
            <p className="text-xs text-purple-200 mt-1">
              Restricted portal for voluntary donor oversight, safety moderation, and platform statistics.
            </p>
          </div>

          {/* Body */}
          <div className="p-8 space-y-6">
            {/* Quick Demo Hint */}
            <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-2xl text-xs text-purple-900 space-y-1">
              <div className="font-bold flex items-center justify-between">
                <span>Default Admin Account:</span>
                <span className="font-mono bg-purple-200/70 px-2 py-0.5 rounded text-[11px] font-black">+91 9876543210</span>
              </div>
              <p className="text-[11px] text-purple-700">
                In development mode, enter <strong>9876543210</strong> and any 6-digit OTP to authenticate.
              </p>
            </div>

            {adminLoginError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3 text-xs text-red-700">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{adminLoginError}</span>
              </div>
            )}

            {adminLoginStep === 'PHONE' ? (
              <form onSubmit={handleSendAdminOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Admin Mobile Number *
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-500">
                      +91
                    </span>
                    <input
                      type="tel"
                      maxLength={10}
                      placeholder="9876543210"
                      value={adminPhone.replace(/^\+91/, '')}
                      onChange={(e) => setAdminPhone(e.target.value.replace(/\D/g, ''))}
                      required
                      autoFocus
                      className="w-full pl-14 pr-4 py-3 text-sm text-slate-900 bg-white border border-slate-300 rounded-xl font-bold focus:ring-2 focus:ring-purple-600 outline-hidden placeholder:text-slate-400"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isAdminLoggingIn || adminPhone.length < 10}
                  className="w-full py-3.5 bg-purple-700 hover:bg-purple-800 active:bg-purple-900 disabled:bg-slate-300 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isAdminLoggingIn ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending Admin OTP...
                    </>
                  ) : (
                    'Request Admin Passcode'
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyAdminLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Enter 6-Digit Admin Passcode
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="• • • • • •"
                    value={adminOtp}
                    onChange={(e) => setAdminOtp(e.target.value.replace(/\D/g, ''))}
                    required
                    autoFocus
                    className="w-full text-center tracking-[0.5em] text-2xl font-bold py-3 text-slate-900 bg-white border border-slate-300 rounded-xl font-mono focus:ring-2 focus:ring-purple-600 outline-hidden placeholder:text-slate-400"
                  />
                  <p className="text-[11px] text-slate-500 text-center mt-2">
                    Passcode dispatched to +91 {adminPhone.replace(/^\+91/, '')}
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <button
                    type="button"
                    onClick={() => setAdminLoginStep('PHONE')}
                    className="text-slate-500 hover:text-slate-800 font-medium cursor-pointer"
                  >
                    Change Number
                  </button>
                  {adminCooldown > 0 ? (
                    <span className="text-slate-400">Resend in {adminCooldown}s</span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSendAdminOtp}
                      className="text-purple-700 font-bold hover:underline cursor-pointer"
                    >
                      Resend Passcode
                    </button>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isAdminLoggingIn || adminOtp.length !== 6}
                  className="w-full py-3.5 bg-purple-700 hover:bg-purple-800 active:bg-purple-900 disabled:bg-slate-300 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isAdminLoggingIn ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Authenticating Admin...
                    </>
                  ) : (
                    'Verify & Open Operations Center'
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 rounded-lg text-xs font-bold text-purple-800 mb-2">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Blood Connect Operations Center</span>
            </div>
            <h1 className="text-3xl font-black text-slate-900">Administrative Dashboard</h1>
            <p className="text-xs sm:text-sm text-slate-600">
              Platform statistics, voluntary donor verification, request oversight, and moderation.
            </p>
          </div>
        </div>

        {/* Banner Alert */}
        {notification && (
          <div
            className={`p-4 rounded-2xl flex items-center justify-between text-xs font-medium border ${
              notification.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            <span>{notification.text}</span>
            <button
              onClick={() => setNotification(null)}
              className="font-bold underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Stats Grid & Blood Group Breakdown (From PDF Spec Page 13) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Total Registered Donors
              </span>
              <Heart className="w-4 h-4 text-red-500 fill-red-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">
              {stats?.total_registered_donors ?? stats?.total_donors ?? 0}
            </div>
            <span className="text-[11px] text-emerald-600 font-semibold">
              {stats?.available_donors ?? 0} currently available
            </span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Total Requests
              </span>
              <Droplet className="w-4 h-4 text-rose-500 fill-rose-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">
              {stats?.requests?.total ?? stats?.total_requests ?? 0}
            </div>
            <span className="text-[11px] text-amber-600 font-semibold">
              {stats?.requests?.pending ?? stats?.pending_requests ?? 0} pending response
            </span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Successful Matches
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">
              {stats?.requests?.accepted ?? stats?.accepted_requests ?? 0}
            </div>
            <span className="text-[11px] text-slate-500">Connections unlocked</span>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Open Reports
              </span>
              <Flag className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">
              {stats?.reports?.open ?? stats?.pending_reports ?? 0}
            </div>
            <span className="text-[11px] text-red-600 font-semibold">
              Needs admin attention
            </span>
          </div>
        </div>

        {/* Blood Groups Distribution Widget (From PDF Spec Page 13 Example) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Droplet className="w-4 h-4 text-red-600 fill-red-600" />
              <span>Blood Groups Distribution (Registered Donors)</span>
            </div>
            <span className="text-xs font-bold text-slate-500">
              Total: {stats?.total_registered_donors ?? stats?.total_donors ?? 0} Donors
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {BLOOD_GROUPS.map((bg) => {
              const count = stats?.donors_by_blood_group?.[bg] ?? 0;
              return (
                <div key={bg} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-center">
                  <span className="block text-xs font-black text-red-600">{bg}</span>
                  <span className="block text-lg font-black text-slate-900 mt-0.5">{count}</span>
                  <span className="block text-[10px] text-slate-400 font-medium">donors</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('DONORS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'DONORS'
                ? 'bg-purple-700 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            Donors Management
          </button>

          <button
            onClick={() => setActiveTab('REQUESTS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'REQUESTS'
                ? 'bg-purple-700 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Droplet className="w-3.5 h-3.5" />
            Requests Oversight
          </button>

          <button
            onClick={() => setActiveTab('REPORTS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'REPORTS'
                ? 'bg-purple-700 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Flag className="w-3.5 h-3.5" />
            Reports & Moderation
            {(stats?.reports?.open ?? stats?.pending_reports ?? 0) > 0 && (
              <span className="px-1.5 py-0.2 bg-red-600 text-white rounded-full text-[10px] font-black">
                {stats?.reports?.open ?? stats?.pending_reports}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('AUDIT')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'AUDIT'
                ? 'bg-purple-700 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Audit Logs
          </button>
        </div>

        {/* ================= TAB 1: DONORS MANAGEMENT ================= */}
        {activeTab === 'DONORS' && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-6">
            {/* Filter Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search donor name or phone..."
                  value={donorSearch}
                  onChange={(e) => setDonorSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadDonors()}
                  className="w-full pl-9 pr-4 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-purple-600 outline-hidden font-medium placeholder:text-slate-400"
                />
              </div>

              <select
                value={donorFilterGroup}
                onChange={(e) => {
                  setDonorFilterGroup(e.target.value);
                  loadDonors();
                }}
                className="px-3 py-2 text-xs text-slate-900 bg-slate-50 border border-slate-300 rounded-xl font-medium focus:ring-2 focus:ring-purple-600 outline-hidden cursor-pointer"
              >
                <option value="">All Blood Groups</option>
                {BLOOD_GROUPS.map((bg) => (
                  <option key={bg} value={bg}>
                    {bg}
                  </option>
                ))}
              </select>

              <select
                value={donorFilterLocation}
                onChange={(e) => {
                  setDonorFilterLocation(e.target.value);
                  loadDonors();
                }}
                className="px-3 py-2 text-xs text-slate-900 bg-slate-50 border border-slate-300 rounded-xl font-medium focus:ring-2 focus:ring-purple-600 outline-hidden cursor-pointer"
              >
                <option value="">All Locations</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Donors Table */}
            {isDonorsLoading ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                <span>Loading donors...</span>
              </div>
            ) : donors.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">No donors found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="p-3">Donor Name</th>
                      <th className="p-3">Blood Group</th>
                      <th className="p-3">Location</th>
                      <th className="p-3">Phone (Admin)</th>
                      <th className="p-3">OTP Status</th>
                      <th className="p-3">Availability</th>
                      <th className="p-3">Account</th>
                      <th className="p-3 text-right">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {donors.map((d) => {
                      const donorName = d.name || d.full_name || 'Donor';
                      const donorMobile = d.mobile || d.user?.mobile || d.user?.mobile_number || '—';
                      const isVerified = d.is_otp_verified ?? d.user?.is_verified ?? true;
                      const isActive = d.is_active ?? d.user?.is_active ?? true;

                      return (
                        <tr key={d.id} className="hover:bg-slate-50/80">
                          <td className="p-3 font-bold text-slate-900">{donorName}</td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded font-black bg-red-100 text-red-800">
                              {d.blood_group}
                            </span>
                          </td>
                          <td className="p-3 text-slate-600">
                            {d.location?.name || '—'}
                          </td>
                          <td className="p-3 text-slate-800 font-mono text-xs">
                            {donorMobile}
                          </td>
                          <td className="p-3">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                isVerified
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              {isVerified ? 'Verified (OTP)' : 'Unverified'}
                            </span>
                          </td>
                          <td className="p-3">
                            <button
                              onClick={() => handleToggleDonorAvailability(d)}
                              className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer ${
                                d.is_available
                                  ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                              }`}
                            >
                              {d.is_available ? 'Available' : 'Cooldown'}
                            </button>
                          </td>
                          <td className="p-3">
                            <button
                              onClick={() => handleToggleDonorStatus(d)}
                              className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer ${
                                isActive
                                  ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                                  : 'bg-red-100 text-red-800 hover:bg-red-200'
                              }`}
                            >
                              {isActive ? 'Active' : 'Suspended'}
                            </button>
                          </td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => setDeleteDonorTarget(d)}
                              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                              title="Remove fake / inappropriate donor"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 2: REQUESTS OVERSIGHT ================= */}
        {activeTab === 'REQUESTS' && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">All Emergency Blood Requests</h3>
            {isRequestsLoading ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                <span>Loading requests...</span>
              </div>
            ) : requests.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">No requests recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="p-3">Patient</th>
                      <th className="p-3">Hospital</th>
                      <th className="p-3">Units</th>
                      <th className="p-3">Urgency</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {requests.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/80">
                        <td className="p-3 font-bold text-slate-900">{r.patient_name}</td>
                        <td className="p-3 text-slate-600">{r.hospital_name}</td>
                        <td className="p-3 font-semibold">{r.required_units}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                            {r.urgency}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.status === 'ACCEPTED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : r.status === 'REJECTED'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-500">
                          {new Date(r.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 3: REPORTS & MODERATION ================= */}
        {activeTab === 'REPORTS' && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Flagged Donor Reports</h3>
            {isReportsLoading ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                <span>Loading reports...</span>
              </div>
            ) : reports.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">No open reports. All clear!</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {reports.map((rep) => (
                  <div key={rep.id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
                          {rep.reason.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {new Date(rep.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-700">{rep.description || 'No additional comments provided.'}</p>
                      <div className="text-[11px] text-slate-500">
                        Donor ID: <strong>#{rep.donor_id}</strong> • Status:{' '}
                        <strong className="uppercase">{rep.status}</strong>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setSelectedReport(rep);
                          setReportActionStatus('RESOLVED');
                        }}
                        className="px-3 py-1.5 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded-xl cursor-pointer"
                      >
                        Action Report
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 4: AUDIT LOGS ================= */}
        {activeTab === 'AUDIT' && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Administrative Audit Trail</h3>
            {isAuditLoading ? (
              <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                <span>Loading audit trail...</span>
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">No audit records logged yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Admin</th>
                      <th className="p-3">Action</th>
                      <th className="p-3">Target</th>
                      <th className="p-3">Details / Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {auditLogs.map((log) => {
                      const adminDisplayName = log.admin_name || (log.admin_id ? `Admin #${log.admin_id}` : 'System');
                      const actionName = log.action || log.action_type || 'ADMIN_ACTION';
                      const detailsText = log.details?.reason || (log.details ? (typeof log.details === 'object' ? JSON.stringify(log.details) : log.details) : log.reason || '—');

                      return (
                        <tr key={log.id} className="hover:bg-slate-50/80">
                          <td className="p-3 text-slate-500">{new Date(log.created_at).toLocaleString()}</td>
                          <td className="p-3 font-bold">{adminDisplayName}</td>
                          <td className="p-3 font-mono text-purple-700">{actionName}</td>
                          <td className="p-3">
                            {log.target_type} #{log.target_id}
                          </td>
                          <td className="p-3 text-slate-600">{detailsText}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ================= MODAL: ACTION REPORT ================= */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
            <div className="bg-purple-900 p-5 text-white flex items-center justify-between">
              <h3 className="text-sm font-bold">Resolve Flagged Report #{selectedReport.id}</h3>
              <button onClick={() => setSelectedReport(null)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveReport} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Set Status</label>
                <select
                  value={reportActionStatus}
                  onChange={(e) => setReportActionStatus(e.target.value as ReportStatus)}
                  className="w-full px-3 py-2 text-xs text-slate-900 bg-slate-50 border border-slate-300 rounded-xl font-medium focus:ring-2 focus:ring-purple-600 outline-hidden cursor-pointer"
                >
                  <option value="RESOLVED">RESOLVED (Action taken)</option>
                  <option value="INVESTIGATING">INVESTIGATING (Under review)</option>
                  <option value="DISMISSED">DISMISSED (Invalid report)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Resolution Notes</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Explain resolution details..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-purple-600 outline-hidden font-medium placeholder:text-slate-400"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedReport(null)}
                  className="px-3 py-1.5 text-xs text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isHandlingReport}
                  className="px-4 py-2 bg-purple-700 text-white text-xs font-bold rounded-xl cursor-pointer"
                >
                  {isHandlingReport ? 'Saving...' : 'Save Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: DELETE DONOR ================= */}
      {deleteDonorTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
            <div className="bg-red-600 p-5 text-white flex items-center justify-between">
              <h3 className="text-sm font-bold">Confirm Donor Deletion</h3>
              <button onClick={() => setDeleteDonorTarget(null)} className="text-white/80 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleDeleteDonor} className="p-6 space-y-4">
              <p className="text-xs text-slate-700">
                Are you sure you want to permanently remove donor <strong>{deleteDonorTarget.name || deleteDonorTarget.full_name}</strong>? This action will be logged in the audit trail.
              </p>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Audit Reason *</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Reason for deletion..."
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  className="w-full px-3 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium placeholder:text-slate-400"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setDeleteDonorTarget(null)}
                  className="px-3 py-1.5 text-xs text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isDeletingDonor}
                  className="px-4 py-2 bg-red-600 text-white text-xs font-bold rounded-xl"
                >
                  {isDeletingDonor ? 'Deleting...' : 'Delete Donor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
