'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Search,
  MapPin,
  Heart,
  Droplet,
  Clock,
  Shield,
  Send,
  Flag,
  AlertCircle,
  CheckCircle2,
  X,
  Loader2,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { BloodGroup, LocationItem, PublicDonor, UrgencyLevel, ReportReason } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const URGENCY_LEVELS: UrgencyLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

function FindDonorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, openLoginModal } = useAuth();

  const [locations, setLocations] = useState<LocationItem[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<BloodGroup | ''>(
    (searchParams.get('blood_group') as BloodGroup) || ''
  );
  const [selectedLocation, setSelectedLocation] = useState<string>(
    searchParams.get('location_id') || ''
  );
  const [searchQuery, setSearchQuery] = useState('');

  const [donors, setDonors] = useState<PublicDonor[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  // Request Modal State
  const [requestModalDonor, setRequestModalDonor] = useState<PublicDonor | null>(null);
  const [patientName, setPatientName] = useState('');
  const [hospitalName, setHospitalName] = useState('');
  const [requiredUnits, setRequiredUnits] = useState(1);
  const [urgency, setUrgency] = useState<UrgencyLevel>('HIGH');
  const [message, setMessage] = useState('');
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  // Report Modal State
  const [reportModalDonor, setReportModalDonor] = useState<PublicDonor | null>(null);
  const [reportReason, setReportReason] = useState<ReportReason>('UNAVAILABLE');
  const [reportDescription, setReportDescription] = useState('');
  const [isSubmittingReport, setIsSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Fetch Locations
  useEffect(() => {
    api.getLocations().then(setLocations).catch(() => {});
  }, []);

  // Fetch Donors
  const fetchDonors = async () => {
    setIsLoading(true);
    try {
      const res = await api.searchDonors({
        blood_group: selectedGroup || undefined,
        location_id: selectedLocation ? parseInt(selectedLocation) : undefined,
        taluk: searchQuery || undefined,
        page: currentPage,
        page_size: 12,
      });
      setDonors(res.items);
      setTotalCount(res.total);
    } catch {
      setDonors([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDonors();
  }, [selectedGroup, selectedLocation, currentPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchDonors();
  };

  const handleOpenRequestModal = (donor: PublicDonor) => {
    if (!isAuthenticated) {
      openLoginModal();
      return;
    }
    setRequestModalDonor(donor);
    setRequestSuccess(false);
    setRequestError(null);
  };

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestModalDonor) return;

    setIsSubmittingRequest(true);
    setRequestError(null);

    try {
      await api.createRequest({
        donor_id: requestModalDonor.id,
        patient_name: patientName,
        hospital_name: hospitalName,
        required_units: Number(requiredUnits),
        urgency,
        message: message || undefined,
      });
      setRequestSuccess(true);
      setPatientName('');
      setHospitalName('');
      setMessage('');
    } catch (err: any) {
      setRequestError(err.message || 'Failed to send request. Please try again.');
    } finally {
      setIsSubmittingRequest(false);
    }
  };

  const handleSubmitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportModalDonor) return;

    if (!isAuthenticated) {
      openLoginModal();
      return;
    }

    setIsSubmittingReport(true);
    setReportError(null);

    try {
      await api.createReport({
        donor_id: reportModalDonor.id,
        reason: reportReason,
        description: reportDescription || undefined,
      });
      setReportSuccess(true);
      setReportDescription('');
    } catch (err: any) {
      setReportError(err.message || 'Failed to file report.');
    } finally {
      setIsSubmittingReport(false);
    }
  };

  return (
    <div className="flex-1 bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 rounded-lg text-xs font-bold text-red-800">
            <Droplet className="w-3.5 h-3.5 fill-red-700" />
            <span>Search & Discover Donors</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            Find Blood Donors in Tamil Nadu
          </h1>
          <p className="text-sm text-slate-600">
            Search voluntary donors by blood type and taluk. Contact details are strictly protected until the donor accepts your request.
          </p>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/80 space-y-6">
          <form onSubmit={handleSearchSubmit} className="space-y-5">
            {/* Blood Groups Selector */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                Filter by Blood Group
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedGroup('');
                    setCurrentPage(1);
                  }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border cursor-pointer ${
                    selectedGroup === ''
                      ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  All Blood Groups
                </button>
                {BLOOD_GROUPS.map((bg) => (
                  <button
                    key={bg}
                    type="button"
                    onClick={() => {
                      setSelectedGroup(selectedGroup === bg ? '' : bg);
                      setCurrentPage(1);
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border cursor-pointer ${
                      selectedGroup === bg
                        ? 'bg-red-600 text-white border-red-600 shadow-md shadow-red-500/20'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-red-50 hover:border-red-200'
                    }`}
                  >
                    {bg}
                  </button>
                ))}
              </div>
            </div>

            {/* Location & Keyword row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Location / Taluk
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <select
                    value={selectedLocation}
                    onChange={(e) => {
                      setSelectedLocation(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                  >
                    <option value="">All Locations (Tamil Nadu)</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.taluk} ({loc.district})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Search Taluk Keyword
                </label>
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="e.g. Sulur, Pollachi, Perur..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-red-500 outline-hidden"
                  />
                </div>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer h-[42px]"
                >
                  <Search className="w-4 h-4" />
                  Apply Filter
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Disclaimer Notice */}
        <MedicalDisclaimer variant="compact" />

        {/* Results Header */}
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-700">
            Showing <span className="text-red-600 font-bold">{donors.length}</span> of {totalCount} voluntary donors found
          </div>
        </div>

        {/* Donors Grid */}
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-500 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-red-600" />
            <p className="text-sm font-medium">Searching matching blood donors...</p>
          </div>
        ) : donors.length === 0 ? (
          <div className="py-16 text-center bg-white rounded-3xl border border-slate-200 p-8 space-y-4">
            <div className="w-14 h-14 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto">
              <AlertCircle className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">No Donors Found Matching Your Criteria</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Try broadening your search by choosing "All Blood Groups" or selecting all Tamil Nadu locations.
            </p>
            <button
              onClick={() => {
                setSelectedGroup('');
                setSelectedLocation('');
                setSearchQuery('');
              }}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-colors cursor-pointer"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {donors.map((donor) => (
              <div
                key={donor.id}
                className="bg-white rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all p-6 flex flex-col justify-between group"
              >
                <div>
                  {/* Top Bar: Group Badge + Availability */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-600 to-rose-700 text-white flex items-center justify-center font-black text-lg shadow-md shadow-red-500/20">
                        {donor.blood_group}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900 group-hover:text-red-600 transition-colors">
                          {donor.full_name}
                        </h3>
                        <span className="text-xs text-slate-500 capitalize">
                          {donor.gender?.toLowerCase()} Donor
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {donor.is_available ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                          Available
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100 text-slate-600">
                          Cooldown
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Donor Details */}
                  <div className="space-y-2.5 py-3 border-y border-slate-100 text-xs text-slate-600">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="font-medium text-slate-800">
                        {donor.location?.taluk}, {donor.location?.district}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span>
                        Last Donated:{' '}
                        <strong className="text-slate-700">
                          {donor.last_donated_at
                            ? new Date(donor.last_donated_at).toLocaleDateString()
                            : 'First Time Donor'}
                        </strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Heart className="w-4 h-4 text-rose-400 flex-shrink-0" />
                      <span>
                        Total Donations:{' '}
                        <strong className="text-slate-700">{donor.total_donations} times</strong>
                      </span>
                    </div>
                  </div>

                  {/* Privacy guarantee text */}
                  <div className="pt-3 pb-4 text-[11px] text-slate-400 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                    <span>Phone number protected until donor accepts</span>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center gap-2 pt-2">
                  <button
                    onClick={() => handleOpenRequestModal(donor)}
                    disabled={!donor.is_available}
                    className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-xs rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Request Contact
                  </button>

                  <button
                    onClick={() => {
                      setReportModalDonor(donor);
                      setReportSuccess(false);
                      setReportError(null);
                    }}
                    className="p-2.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                    title="Report profile issue"
                  >
                    <Flag className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ================= SEND REQUEST MODAL ================= */}
      {requestModalDonor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-600 to-rose-700 p-6 text-white relative">
              <button
                onClick={() => setRequestModalDonor(null)}
                className="absolute top-4 right-4 text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-white font-bold text-lg backdrop-blur-xs">
                  {requestModalDonor.blood_group}
                </div>
                <div>
                  <h3 className="text-lg font-bold">Request Blood from {requestModalDonor.full_name}</h3>
                  <p className="text-xs text-rose-100">
                    Location: {requestModalDonor.location?.taluk}, {requestModalDonor.location?.district}
                  </p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6">
              {requestSuccess ? (
                <div className="text-center py-6 space-y-4">
                  <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-bold text-slate-800">Blood Request Sent Successfully!</h4>
                  <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
                    The donor has been notified via in-app alert. As soon as they accept, their verified phone number will unlock on your dashboard.
                  </p>
                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      onClick={() => {
                        setRequestModalDonor(null);
                        router.push('/requester/dashboard');
                      }}
                      className="w-full py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer"
                    >
                      Go to Sent Requests Dashboard
                    </button>
                    <button
                      onClick={() => setRequestModalDonor(null)}
                      className="text-xs text-slate-500 hover:text-slate-800 font-medium py-1"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmitRequest} className="space-y-4">
                  {requestError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs text-red-700">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{requestError}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Patient Full Name *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. K. Ramesh"
                        value={patientName}
                        onChange={(e) => setPatientName(e.target.value)}
                        className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Required Units (Bags) *
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={10}
                        required
                        value={requiredUnits}
                        onChange={(e) => setRequiredUnits(parseInt(e.target.value) || 1)}
                        className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Hospital Name & City *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. KMCH Hospital, Avinashi Road, Coimbatore"
                      value={hospitalName}
                      onChange={(e) => setHospitalName(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Emergency Urgency Level *
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {URGENCY_LEVELS.map((lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setUrgency(lvl)}
                          className={`py-2 px-1 rounded-xl text-[11px] font-bold border transition-all cursor-pointer ${
                            urgency === lvl
                              ? lvl === 'CRITICAL'
                                ? 'bg-red-600 text-white border-red-600'
                                : lvl === 'HIGH'
                                ? 'bg-amber-600 text-white border-amber-600'
                                : 'bg-slate-800 text-white border-slate-800'
                              : 'bg-slate-50 text-slate-700 border-slate-200'
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Optional Medical Message / Notes
                    </label>
                    <textarea
                      rows={2}
                      placeholder="Doctor name, ward number, or emergency details..."
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
                    />
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-500 leading-relaxed">
                    By submitting, your registered phone number will be shared with the donor upon acceptance for direct coordination.
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setRequestModalDonor(null)}
                      className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmittingRequest}
                      className="py-2.5 px-6 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-300 text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer"
                    >
                      {isSubmittingRequest ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        'Send Blood Request'
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ================= REPORT MODAL ================= */}
      {reportModalDonor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
            <div className="bg-slate-900 p-5 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flag className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold">Report Donor Profile</h3>
              </div>
              <button
                onClick={() => setReportModalDonor(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6">
              {reportSuccess ? (
                <div className="text-center py-4 space-y-3">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                  <h4 className="text-sm font-bold text-slate-800">Report Submitted</h4>
                  <p className="text-xs text-slate-600">
                    Our admin team will review this report. Thank you for keeping Blood Connect safe and authentic.
                  </p>
                  <button
                    onClick={() => setReportModalDonor(null)}
                    className="mt-2 px-4 py-2 bg-slate-900 text-white text-xs font-bold rounded-xl"
                  >
                    Close
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmitReport} className="space-y-4">
                  {reportError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                      {reportError}
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Reason for Report *
                    </label>
                    <select
                      value={reportReason}
                      onChange={(e) => setReportReason(e.target.value as ReportReason)}
                      className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-xl font-medium text-slate-800"
                    >
                      <option value="UNAVAILABLE">Donor is permanently unavailable</option>
                      <option value="INCORRECT_CONTACT">Invalid or unreachable contact</option>
                      <option value="INELIGIBLE_DONOR">Medical ineligibility</option>
                      <option value="SUSPICIOUS_BEHAVIOR">Commercial / Suspicious behavior</option>
                      <option value="OTHER">Other issue</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Additional Details
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Please explain the issue..."
                      value={reportDescription}
                      onChange={(e) => setReportDescription(e.target.value)}
                      className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setReportModalDonor(null)}
                      className="px-3 py-1.5 text-xs text-slate-600"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmittingReport}
                      className="px-4 py-2 bg-red-600 text-white text-xs font-bold rounded-xl"
                    >
                      {isSubmittingReport ? 'Submitting...' : 'Submit Report'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function FindDonorPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-slate-500">Loading donor search...</div>}>
      <FindDonorContent />
    </Suspense>
  );
}
