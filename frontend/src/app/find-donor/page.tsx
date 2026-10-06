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
  User as UserIcon,
  Phone,
  KeyRound,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react';
import { BloodGroup, LocationItem, PublicDonor, UrgencyLevel, ReportReason } from '@/types';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';
import { DEFAULT_LOCATIONS } from '@/lib/constants';

const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const URGENCY_LEVELS: UrgencyLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];


interface LastPatientDetails {
  patient_name: string;
  hospital_name: string;
  required_units: number;
  urgency: UrgencyLevel;
  message?: string;
  saved_at?: string;
}

function FindDonorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuth();

  const [locations, setLocations] = useState<LocationItem[]>(DEFAULT_LOCATIONS);
  const [selectedGroup, setSelectedGroup] = useState<BloodGroup | ''>(
    (searchParams.get('blood_group') as BloodGroup) || ''
  );
  const [locationQuery, setLocationQuery] = useState<string>(
    searchParams.get('location') || searchParams.get('taluk') || ''
  );

  const hasFilterEntered = Boolean(selectedGroup || locationQuery.trim());

  const [donors, setDonors] = useState<PublicDonor[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  // Request Modal State
  const [requestModalDonor, setRequestModalDonor] = useState<PublicDonor | null>(null);
  const [requestStep, setRequestStep] = useState<'FORM' | 'SUCCESS'>('FORM');
  const [restoredNotice, setRestoredNotice] = useState(false);

  const [lastPatientDetails, setLastPatientDetails] = useState<LastPatientDetails | null>(null);
  const [patientName, setPatientName] = useState('');
  const [hospitalName, setHospitalName] = useState('');
  const [requiredUnits, setRequiredUnits] = useState(1);
  const [urgency, setUrgency] = useState<UrgencyLevel>('HIGH');
  const [message, setMessage] = useState('');
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  // Automatically restore pending blood request after returning from login
  useEffect(() => {
    if (isAuthenticated && typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('bloodconnect_pending_request');
        if (saved) {
          const pending = JSON.parse(saved);
          if (pending && pending.donor) {
            setRequestModalDonor(pending.donor);
            setPatientName(pending.patient_name || '');
            setHospitalName(pending.hospital_name || '');
            setRequiredUnits(pending.required_units || 1);
            setUrgency(pending.urgency || 'HIGH');
            setMessage(pending.message || '');
            setRequestStep('FORM');
            setRequestError(null);
            setRestoredNotice(true);
            localStorage.removeItem('bloodconnect_pending_request');
          }
        }
      } catch (err) {
        console.error('Failed to restore pending request:', err);
      }
    }
  }, [isAuthenticated]);

  // Report Modal State
  const [reportModalDonor, setReportModalDonor] = useState<PublicDonor | null>(null);
  const [reportReason, setReportReason] = useState<ReportReason>('INCORRECT_INFORMATION');
  const [reportDescription, setReportDescription] = useState('');
  const [isSubmittingReport, setIsSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Fetch Locations
  useEffect(() => {
    api.getLocations().then((data) => {
      if (data && data.length > 0) setLocations(data);
    }).catch(() => {});
  }, []);

  // Fetch Donors (Only when filter criteria are provided)
  const fetchDonors = async () => {
    if (!selectedGroup && !locationQuery.trim()) {
      setDonors([]);
      setTotalCount(0);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.searchDonors({
        blood_group: selectedGroup || undefined,
        location: locationQuery.trim() || undefined,
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
    if (selectedGroup || locationQuery.trim()) {
      fetchDonors();
    } else {
      setDonors([]);
      setTotalCount(0);
      setIsLoading(false);
    }
  }, [selectedGroup, locationQuery, currentPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchDonors();
  };

  const normalizePhone = (num: string) => {
    const cleaned = num.replace(/\D/g, '');
    if (cleaned.length === 10) return `+91${cleaned}`;
    if (cleaned.length === 12 && cleaned.startsWith('91')) return `+${cleaned}`;
    if (num.startsWith('+91') && cleaned.length === 12) return num;
    return `+91${cleaned}`;
  };

  const handleOpenRequestModal = (donor: PublicDonor) => {
    setRequestModalDonor(donor);
    setRequestStep('FORM');
    setRequestError(null);
    setRestoredNotice(false);

    // Check last patient details from localStorage for 1-click multiple donor requests
    let savedPatient: LastPatientDetails | null = null;
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('bloodconnect_last_patient');
        if (saved) {
          const parsed: LastPatientDetails = JSON.parse(saved);
          if (parsed && parsed.patient_name && parsed.hospital_name) {
            savedPatient = parsed;
          }
        }
      } catch {}
    }

    if (savedPatient) {
      setLastPatientDetails(savedPatient);
      setPatientName(savedPatient.patient_name);
      setHospitalName(savedPatient.hospital_name);
      setRequiredUnits(savedPatient.required_units || 1);
      setUrgency(savedPatient.urgency || 'HIGH');
      setMessage(savedPatient.message || '');
    } else {
      setLastPatientDetails(null);
      setPatientName('');
      setHospitalName('');
      setRequiredUnits(1);
      setUrgency('HIGH');
      setMessage('');
    }
  };

  const savePatientDetailsToStorage = (override?: Partial<LastPatientDetails>) => {
    const pName = (override?.patient_name !== undefined ? override.patient_name : patientName).trim();
    const hName = (override?.hospital_name !== undefined ? override.hospital_name : hospitalName).trim();
    const units = override?.required_units !== undefined ? override.required_units : (Number(requiredUnits) || 1);
    const urg = override?.urgency !== undefined ? override.urgency : urgency;
    const msg = (override?.message !== undefined ? override.message : message).trim();

    if (pName && hName) {
      const patientData: LastPatientDetails = {
        patient_name: pName,
        hospital_name: hName,
        required_units: units,
        urgency: urg,
        message: msg || undefined,
        saved_at: new Date().toISOString(),
      };
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('bloodconnect_last_patient', JSON.stringify(patientData));
        } catch {}
      }
      setLastPatientDetails(patientData);
      return patientData;
    }
    return null;
  };

  const handleSubmitRequestForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestModalDonor) return;
    setRequestError(null);

    if (!patientName.trim()) {
      setRequestError('Please enter the patient full name.');
      return;
    }
    if (!hospitalName.trim()) {
      setRequestError('Please enter the hospital name and city.');
      return;
    }

    // Immediately persist patient details for autofill convenience
    savePatientDetailsToStorage();

    // If unauthenticated: save pending request draft and redirect to login page
    if (!isAuthenticated) {
      const pendingData = {
        donor: requestModalDonor,
        patient_name: patientName.trim(),
        hospital_name: hospitalName.trim(),
        required_units: Number(requiredUnits) || 1,
        urgency,
        message: message.trim(),
        saved_at: new Date().toISOString(),
      };
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('bloodconnect_pending_request', JSON.stringify(pendingData));
        } catch {}
      }
      router.push('/login?redirect=/find-donor');
      return;
    }

    // If already authenticated: directly dispatch request
    setIsSubmittingRequest(true);
    try {
      await api.createRequest({
        donor_id: requestModalDonor.id,
        patient_name: patientName.trim(),
        hospital_name: hospitalName.trim(),
        required_units: Number(requiredUnits),
        urgency,
        message: message.trim() || undefined,
        blood_group: requestModalDonor.blood_group,
        location_id: requestModalDonor.location?.id,
      });

      setRequestStep('SUCCESS');
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
      setReportError('Please sign in to submit a report.');
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 rounded-full text-xs font-bold text-red-800">
            <Droplet className="w-3.5 h-3.5 fill-red-700" />
            <span>Search & Discover Donors</span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-slate-900 tracking-tight">
            Find Blood Donors {locationQuery ? `in ${locationQuery}` : 'across Coimbatore'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-2xl font-medium">
            Search verified voluntary blood donors by blood type and locality. Direct contact numbers unlock immediately upon request acceptance.
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

            {/* Location Dropdown Row */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">
                Select Location / Area
              </label>
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <select
                    value={locationQuery}
                    onChange={(e) => {
                      setLocationQuery(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full pl-10 pr-8 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                  >
                    <option value="">Select Location / Area</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.name}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  className="py-2.5 px-6 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer h-[42px]"
                >
                  <Search className="w-4 h-4" />
                  Search Donors
                </button>

                {locationQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setLocationQuery('');
                      setCurrentPage(1);
                      api.searchDonors({ blood_group: selectedGroup || undefined, page: 1, page_size: 12 }).then((r) => {
                        setDonors(r.items);
                        setTotalCount(r.total);
                      });
                    }}
                    className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer h-[42px]"
                  >
                    Clear Location
                  </button>
                )}
              </div>

              {/* Quick Location Pills */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs">
                <span className="text-[11px] text-slate-400 font-medium">Quick suggestions:</span>
                {locations.slice(0, 6).map((loc) => (
                  <button
                    key={loc.id}
                    type="button"
                    onClick={() => {
                      setLocationQuery(loc.name);
                      setCurrentPage(1);
                      api.searchDonors({
                        blood_group: selectedGroup || undefined,
                        location: loc.name,
                        page: 1,
                        page_size: 12,
                      }).then((r) => {
                        setDonors(r.items);
                        setTotalCount(r.total);
                      });
                    }}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors cursor-pointer ${
                      locationQuery.toLowerCase() === loc.name.toLowerCase()
                        ? 'bg-red-600 text-white shadow-xs'
                        : 'bg-slate-100 hover:bg-red-50 text-slate-700 hover:text-red-700 border border-slate-200'
                    }`}
                  >
                    {loc.name}
                  </button>
                ))}
              </div>
            </div>
          </form>
        </div>

        {/* Cleanly Contained Disclaimer Notice */}
        <div>
          <MedicalDisclaimer variant="compact" />
        </div>

        {/* Results Area */}
        {!hasFilterEntered ? (
          /* Initial State: Prompt user to enter search filters */
          <div className="py-16 text-center bg-white rounded-3xl border border-slate-200/90 p-8 md:p-12 space-y-5 shadow-xs">
            <div className="w-16 h-16 bg-red-50 text-red-600 rounded-3xl flex items-center justify-center mx-auto shadow-inner">
              <Search className="w-8 h-8 text-red-600" />
            </div>
            <div className="space-y-1.5 max-w-md mx-auto">
              <h3 className="text-xl font-black text-slate-900">
                Search for Voluntary Donors
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed font-medium">
                Please select a <strong>Blood Group</strong> or choose a <strong>Location / Area</strong> from the filters above to find matching blood donors.
              </p>
            </div>
            <div className="pt-2 flex flex-wrap justify-center items-center gap-2">
              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block w-full mb-1">
                Quick Blood Group Selection:
              </span>
              {BLOOD_GROUPS.map((bg) => (
                <button
                  key={bg}
                  type="button"
                  onClick={() => {
                    setSelectedGroup(bg);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-50 hover:bg-red-600 hover:text-white text-slate-700 border border-slate-200 hover:border-red-600 transition-all cursor-pointer shadow-xs hover:shadow-md"
                >
                  {bg}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-700">
                Showing <span className="text-red-600 font-bold">{donors.length}</span> of {totalCount} voluntary donors found
                {selectedGroup && (
                  <span className="text-slate-800 font-bold"> for {selectedGroup}</span>
                )}
                {locationQuery && (
                  <span className="text-slate-500 font-normal"> in "{locationQuery}"</span>
                )}
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
                  Try choosing a different blood group or clearing the location filter.
                </p>
                <button
                  onClick={() => {
                    setSelectedGroup('');
                    setLocationQuery('');
                    setCurrentPage(1);
                    setDonors([]);
                    setTotalCount(0);
                  }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-colors cursor-pointer"
                >
                  Reset All Filters
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
                              {donor.full_name || donor.name}
                            </h3>
                            <span className="text-xs font-semibold text-slate-500">
                              {donor.age ? `${donor.age} Years Old` : 'Eligible Voluntary Donor'}
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
                              Unavailable
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Donor Details: ONLY Name, Age, Blood Group, Location */}
                      <div className="space-y-2 py-3 border-y border-slate-100 text-xs text-slate-600">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-medium">Age:</span>
                          <span className="font-bold text-slate-800">
                            {donor.age ? `${donor.age} Years` : '18+ Years'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-medium">Blood Group:</span>
                          <span className="font-black text-red-600 bg-red-50 px-2 py-0.5 rounded-md">
                            {donor.blood_group}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-medium">Location:</span>
                          <div className="flex items-center gap-1 font-bold text-slate-800">
                            <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                            <span>{donor.location?.name}</span>
                          </div>
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
                        className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-700 active:bg-red-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-xs rounded-xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed min-h-[44px]"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Request Contact</span>
                      </button>

                      <button
                        onClick={() => {
                          setReportModalDonor(donor);
                          setReportSuccess(false);
                          setReportError(null);
                        }}
                        className="p-3 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center"
                        title="Report profile issue"
                      >
                        <Flag className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* ================= SEND REQUEST MODAL WITH REQUESTER SIGNIN / SIGNUP ================= */}
      {requestModalDonor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-600 to-rose-700 p-6 text-white relative flex-shrink-0">
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
                    Location: {requestModalDonor.location?.name}
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1">
              {requestStep === 'SUCCESS' ? (
                <div className="text-center py-6 space-y-4">
                  <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-bold text-slate-800">Blood Request Sent Successfully!</h4>
                  <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
                    Your request has been dispatched to <strong>{requestModalDonor.full_name}</strong>. As soon as they accept, their verified phone number will unlock on your dashboard for direct coordination.
                  </p>
                  <div className="pt-2 flex flex-col sm:flex-row gap-2">
                    <button
                      onClick={() => setRequestModalDonor(null)}
                      className="flex-1 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <Search className="w-3.5 h-3.5" />
                      <span>Request Another Donor</span>
                    </button>
                    <button
                      onClick={() => {
                        setRequestModalDonor(null);
                        router.push('/requester/dashboard');
                      }}
                      className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer"
                    >
                      View Sent Requests
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmitRequestForm} className="space-y-4">
                  {requestError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs text-red-700">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{requestError}</span>
                    </div>
                  )}

                  {/* Restored from Login Success Banner */}
                  {restoredNotice && isAuthenticated && (
                    <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between gap-2.5 text-xs text-emerald-800 animate-in fade-in">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>
                          Welcome back, <strong>{user?.name}</strong>! Your request details have been restored. Review and click below to send.
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setRestoredNotice(false)}
                        className="text-emerald-500 hover:text-emerald-700 p-0.5 cursor-pointer"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Authenticated Requester Info Banner */}
                  {isAuthenticated ? (
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
                          <UserIcon className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="block font-bold text-slate-900">{user?.name}</span>
                          <span className="block text-[11px] text-slate-500">{user?.mobile || user?.mobile_number}</span>
                        </div>
                      </div>
                      <div className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100/80 px-2.5 py-1 rounded-full">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Verified Account</span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-2xl flex items-start gap-3 text-xs text-amber-900">
                      <Shield className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold">Sign in required to request donor contact</span>
                        <p className="text-[11px] text-amber-700 mt-0.5 leading-relaxed">
                          Fill in the patient requirement below and click Continue. Your details will be preserved and you will return right here to dispatch your blood request with 1 tap.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Patient and Emergency Blood Details */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                        Patient & Requirement Information
                      </div>
                    </div>

                    {/* Compact Smart Autofill Chip */}
                    {lastPatientDetails && (
                      <div className="p-3 bg-red-50/90 border border-red-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs animate-in fade-in">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-red-600 shrink-0" />
                          <span className="text-slate-700 font-medium">
                            Recent patient: <strong className="text-slate-900">{lastPatientDetails.patient_name}</strong> ({lastPatientDetails.hospital_name}, {lastPatientDetails.required_units} Bags)
                          </span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {patientName.trim().toLowerCase() !== lastPatientDetails.patient_name.toLowerCase() ? (
                            <button
                              type="button"
                              onClick={() => {
                                setPatientName(lastPatientDetails.patient_name);
                                setHospitalName(lastPatientDetails.hospital_name);
                                setRequiredUnits(lastPatientDetails.required_units || 1);
                                setUrgency(lastPatientDetails.urgency || 'HIGH');
                                setMessage(lastPatientDetails.message || '');
                              }}
                              className="px-2.5 py-1 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-2xs text-[11px] cursor-pointer"
                            >
                              Autofill
                            </button>
                          ) : (
                            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md">
                              Filled
                            </span>
                          )}
                          <button
                            type="button"
                            onClick={() => {
                              setLastPatientDetails(null);
                              try { localStorage.removeItem('bloodconnect_last_patient'); } catch {}
                            }}
                            className="text-[11px] text-slate-400 hover:text-slate-600 cursor-pointer"
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                          className="w-full px-3.5 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium placeholder:text-slate-400"
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
                          className="w-full px-3.5 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium"
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
                        className="w-full px-3.5 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium placeholder:text-slate-400"
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
                        className="w-full px-3.5 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium placeholder:text-slate-400"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setRequestModalDonor(null)}
                      className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 cursor-pointer"
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
                          Processing...
                        </>
                      ) : !isAuthenticated ? (
                        <>
                          <span>Continue to Sign In</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5" />
                          <span>Send Blood Request</span>
                        </>
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
                      className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-red-500 outline-hidden cursor-pointer"
                    >
                      <option value="INCORRECT_INFORMATION">Incorrect Information</option>
                      <option value="FAKE_PROFILE">Fake Profile</option>
                      <option value="WRONG_BLOOD_GROUP">Wrong Blood Group</option>
                      <option value="SPAM">Spam</option>
                      <option value="MISUSE">Commercial / Misuse</option>
                      <option value="OTHER">Other Issue</option>
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
                      className="w-full px-3 py-2 text-xs text-slate-900 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-hidden font-medium placeholder:text-slate-400"
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
