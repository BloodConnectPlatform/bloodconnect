'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Heart,
  Droplet,
  MapPin,
  Clock,
  Phone,
  MessageSquare,
  CheckCircle2,
  XCircle,
  AlertCircle,
  UserCheck,
  Edit3,
  Loader2,
  Calendar,
  ShieldCheck,
  Building,
  Activity,
} from 'lucide-react';
import { BloodRequest, DonorProfile, LocationItem } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';

export default function DonorDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, setDonorProfile: setGlobalDonorProfile } = useAuth();

  const [profile, setProfile] = useState<DonorProfile | null>(null);
  const [pendingRequests, setPendingRequests] = useState<BloodRequest[]>([]);
  const [acceptedRequests, setAcceptedRequests] = useState<BloodRequest[]>([]);
  const [allRequests, setAllRequests] = useState<BloodRequest[]>([]);
  const [locations, setLocations] = useState<LocationItem[]>([]);

  const [activeTab, setActiveTab] = useState<'PENDING' | 'ACCEPTED' | 'ALL'>('PENDING');
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Edit Profile Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editLocationId, setEditLocationId] = useState<number | ''>('');
  const [editLastDonated, setEditLastDonated] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDonorDashboard();
      setProfile(data.profile);
      setGlobalDonorProfile(data.profile);
      setPendingRequests(data.pending_requests);
      setAcceptedRequests(data.accepted_requests);
      setAllRequests(data.recent_requests);

      if (data.profile) {
        setEditName(data.profile.full_name);
        setEditLocationId(data.profile.location_id);
        setEditLastDonated(
          data.profile.last_donated_at
            ? new Date(data.profile.last_donated_at).toISOString().split('T')[0]
            : ''
        );
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to load dashboard data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
      api.getLocations().then(setLocations).catch(() => {});
    }
  }, [isAuthenticated]);

  const handleToggleAvailability = async () => {
    if (!profile) return;
    try {
      const newStatus = !profile.is_available;
      const updated = await api.toggleAvailability(newStatus);
      setProfile(updated);
      setGlobalDonorProfile(updated);
      setMessage({
        type: 'success',
        text: `Your availability status is now set to ${newStatus ? 'AVAILABLE' : 'UNAVAILABLE (COOLDOWN)'}.`,
      });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update availability.' });
    }
  };

  const handleAcceptRequest = async (requestId: number) => {
    setActionLoadingId(requestId);
    setMessage(null);
    try {
      await api.acceptRequest(requestId);
      setMessage({
        type: 'success',
        text: 'Request accepted! Requester contact details are now unlocked below.',
      });
      await fetchDashboardData();
      setActiveTab('ACCEPTED');
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to accept request.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    setActionLoadingId(requestId);
    setMessage(null);
    try {
      await api.rejectRequest(requestId);
      setMessage({
        type: 'success',
        text: 'Request declined.',
      });
      await fetchDashboardData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to reject request.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;

    setIsSavingProfile(true);
    try {
      const updated = await api.updateDonorProfile({
        full_name: editName,
        location_id: editLocationId ? Number(editLocationId) : undefined,
        last_donated_at: editLastDonated ? new Date(editLastDonated).toISOString() : null,
      });
      setProfile(updated);
      setGlobalDonorProfile(updated);
      setIsEditModalOpen(false);
      setMessage({ type: 'success', text: 'Donor profile updated successfully.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update profile.' });
    } finally {
      setIsSavingProfile(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <p className="text-sm font-medium">Loading Donor Hub...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-xl mx-auto py-16 px-4 text-center space-y-4">
        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center mx-auto">
          <Heart className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-800">No Donor Profile Found</h2>
        <p className="text-xs text-slate-600">
          You are currently logged in with a general account. Please complete donor registration to access this hub.
        </p>
        <button
          onClick={() => router.push('/register')}
          className="px-6 py-2.5 bg-red-600 text-white text-xs font-bold rounded-xl shadow-xs"
        >
          Register as Donor
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Banner Alert */}
        {message && (
          <div
            className={`p-4 rounded-2xl flex items-center justify-between text-xs font-medium border ${
              message.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)} className="font-bold underline cursor-pointer">
              Dismiss
            </button>
          </div>
        )}

        {/* Profile Card & Availability Control */}
        <div className="bg-white rounded-3xl p-6 md:p-8 shadow-xs border border-slate-200/80">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Left: Donor info */}
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-600 to-rose-700 text-white flex items-center justify-center font-black text-2xl shadow-md shadow-red-500/20">
                {profile.blood_group}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-black text-slate-900">{profile.full_name}</h1>
                  <button
                    onClick={() => setIsEditModalOpen(true)}
                    className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Edit profile"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 font-medium">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {profile.location?.name}, {profile.location?.district}
                  </span>
                  <span>•</span>
                  <span>Registered: {user?.mobile_number}</span>
                  <span>•</span>
                  <span>Total Donations: {profile.total_donations}</span>
                </div>
              </div>
            </div>

            {/* Right: Availability Toggle Control */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
              <div className="space-y-0.5">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Donation Availability
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      profile.is_available ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                    }`}
                  />
                  <span className="text-sm font-bold text-slate-800">
                    {profile.is_available ? 'Ready for Emergency Calls' : 'Currently Unavailable (Cooldown)'}
                  </span>
                </div>
              </div>

              <button
                onClick={handleToggleAvailability}
                className={`py-2.5 px-5 rounded-xl font-bold text-xs transition-all cursor-pointer shadow-xs ${
                  profile.is_available
                    ? 'bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300'
                    : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20'
                }`}
              >
                {profile.is_available ? 'Set as Unavailable' : 'Set as Available'}
              </button>
            </div>
          </div>
        </div>

        {/* Requests Management Section */}
        <div className="space-y-4">
          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <button
              onClick={() => setActiveTab('PENDING')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                activeTab === 'PENDING'
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              Pending Requests
              {pendingRequests.length > 0 && (
                <span className="px-1.5 py-0.2 bg-white text-red-600 rounded-full text-[10px] font-black">
                  {pendingRequests.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('ACCEPTED')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                activeTab === 'ACCEPTED'
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Accepted & Active ({acceptedRequests.length})
            </button>

            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                activeTab === 'ALL'
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              History ({allRequests.length})
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'PENDING' && (
            <div className="space-y-4">
              {pendingRequests.length === 0 ? (
                <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                  <h3 className="text-base font-bold text-slate-800">No Pending Requests</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    You have responded to all incoming requests. When a patient in your area requests your blood type, it will appear right here.
                  </p>
                </div>
              ) : (
                pendingRequests.map((req) => (
                  <div
                    key={req.id}
                    className="bg-white rounded-2xl p-6 border-2 border-red-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                            req.urgency === 'CRITICAL'
                              ? 'bg-red-600 text-white'
                              : req.urgency === 'HIGH'
                              ? 'bg-amber-500 text-white'
                              : 'bg-slate-800 text-white'
                          }`}
                        >
                          {req.urgency} Urgency
                        </span>
                        <span className="text-xs text-slate-400">
                          Received {new Date(req.created_at).toLocaleString()}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-slate-900">
                        {req.patient_name} — {req.required_units} Unit(s) Needed
                      </h3>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600">
                        <span className="flex items-center gap-1 font-medium">
                          <Building className="w-3.5 h-3.5 text-slate-400" />
                          {req.hospital_name}
                        </span>
                        {req.message && (
                          <span className="italic text-slate-500">"{req.message}"</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleRejectRequest(req.id)}
                        disabled={actionLoadingId === req.id}
                        className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer"
                      >
                        Decline
                      </button>

                      <button
                        onClick={() => handleAcceptRequest(req.id)}
                        disabled={actionLoadingId === req.id}
                        className="py-2.5 px-6 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold text-xs rounded-xl shadow-md shadow-red-500/20 transition-all flex items-center gap-2 cursor-pointer"
                      >
                        {actionLoadingId === req.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                        Accept & Share Phone
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'ACCEPTED' && (
            <div className="space-y-4">
              {acceptedRequests.length === 0 ? (
                <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 space-y-2">
                  <Activity className="w-10 h-10 text-slate-400 mx-auto" />
                  <h3 className="text-base font-bold text-slate-800">No Accepted Requests Yet</h3>
                  <p className="text-xs text-slate-500">
                    Requests you accept will appear here with direct contact details for coordination.
                  </p>
                </div>
              ) : (
                acceptedRequests.map((req) => (
                  <div
                    key={req.id}
                    className="bg-white rounded-2xl p-6 border border-emerald-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-100 text-emerald-800">
                          ACCEPTED & CONNECTED
                        </span>
                        <span className="text-xs text-slate-400">
                          {new Date(req.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-slate-900">
                        Patient: {req.patient_name} ({req.required_units} Units)
                      </h3>

                      <div className="text-xs text-slate-600 font-medium">
                        Hospital: {req.hospital_name}
                      </div>

                      {/* Unlocked Requester Phone */}
                      {req.requester_contact && (
                        <div className="mt-2 inline-flex items-center gap-3 p-2.5 bg-emerald-50 rounded-xl border border-emerald-200 text-xs font-bold text-emerald-900">
                          <Phone className="w-4 h-4 text-emerald-600" />
                          <span>Requester Phone: {req.requester_contact}</span>
                        </div>
                      )}
                    </div>

                    {req.requester_contact && (
                      <div className="flex items-center gap-2">
                        <a
                          href={`tel:${req.requester_contact}`}
                          className="py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 shadow-xs"
                        >
                          <Phone className="w-3.5 h-3.5" />
                          Call Requester
                        </a>
                        <a
                          href={`https://wa.me/${req.requester_contact.replace(/\D/g, '')}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="py-2 px-4 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 shadow-xs"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          WhatsApp
                        </a>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'ALL' && (
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="p-4">Patient / Hospital</th>
                      <th className="p-4">Units</th>
                      <th className="p-4">Urgency</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {allRequests.map((req) => (
                      <tr key={req.id} className="hover:bg-slate-50/80">
                        <td className="p-4 font-bold text-slate-800">
                          <div>{req.patient_name}</div>
                          <div className="font-normal text-slate-500">{req.hospital_name}</div>
                        </td>
                        <td className="p-4 font-semibold">{req.required_units}</td>
                        <td className="p-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                            {req.urgency}
                          </span>
                        </td>
                        <td className="p-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              req.status === 'ACCEPTED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : req.status === 'REJECTED'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {req.status}
                          </span>
                        </td>
                        <td className="p-4 text-slate-500">
                          {new Date(req.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Disclaimer Reminder */}
        <MedicalDisclaimer variant="card" />
      </div>

      {/* ================= EDIT PROFILE MODAL ================= */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
            <div className="bg-slate-900 p-5 text-white flex items-center justify-between">
              <h3 className="text-sm font-bold">Edit Donor Profile</h3>
              <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Primary Location / Area</label>
                <select
                  value={editLocationId}
                  onChange={(e) => setEditLocationId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-xl"
                >
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name} ({loc.district})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Last Donated Date</label>
                <input
                  type="date"
                  value={editLastDonated}
                  onChange={(e) => setEditLastDonated(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingProfile}
                  className="px-4 py-2 bg-red-600 text-white text-xs font-bold rounded-xl"
                >
                  {isSavingProfile ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
