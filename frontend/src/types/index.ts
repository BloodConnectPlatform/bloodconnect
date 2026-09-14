export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-';
export type UserRole = 'DONOR' | 'REQUESTER' | 'ADMIN';
export type RequestStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED' | 'FULFILLED';
export type UrgencyLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ReportReason = 'INCORRECT_CONTACT' | 'UNAVAILABLE' | 'INELIGIBLE_DONOR' | 'SUSPICIOUS_BEHAVIOR' | 'OTHER';
export type ReportStatus = 'PENDING' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';
export type NotificationType = 'REQUEST_RECEIVED' | 'REQUEST_ACCEPTED' | 'REQUEST_REJECTED' | 'SYSTEM';
export type Gender = 'MALE' | 'FEMALE' | 'OTHER';

export interface LocationItem {
  id: number;
  district: string;
  taluk: string;
  pincode?: string;
  is_active: boolean;
}

export interface User {
  id: number;
  mobile_number: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface DonorProfile {
  id: number;
  user_id: number;
  full_name: string;
  blood_group: BloodGroup;
  gender: Gender;
  date_of_birth: string;
  location_id: number;
  is_available: boolean;
  last_donated_at?: string;
  total_donations: number;
  created_at: string;
  location: LocationItem;
  user?: User;
}

export interface PublicDonor {
  id: number;
  full_name: string;
  blood_group: BloodGroup;
  gender: Gender;
  location: LocationItem;
  is_available: boolean;
  last_donated_at?: string;
  total_donations: number;
  created_at: string;
}

export interface BloodRequest {
  id: number;
  requester_id: number;
  donor_id: number;
  patient_name: string;
  hospital_name: string;
  required_units: number;
  urgency: UrgencyLevel;
  message?: string;
  status: RequestStatus;
  created_at: string;
  updated_at?: string;
  // Disclosed strictly when status is ACCEPTED
  donor_contact?: string;
  requester_contact?: string;
  donor?: PublicDonor;
  requester?: {
    id: number;
    mobile_number?: string;
  };
}

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: NotificationType;
  is_read: boolean;
  reference_id?: number;
  created_at: string;
}

export interface ReportItem {
  id: number;
  reporter_id: number;
  donor_id: number;
  reason: ReportReason;
  description?: string;
  status: ReportStatus;
  resolution_notes?: string;
  created_at: string;
  donor?: PublicDonor;
}

export interface AdminStats {
  total_users: number;
  total_donors: number;
  available_donors: number;
  total_requests: number;
  pending_requests: number;
  accepted_requests: number;
  total_reports: number;
  pending_reports: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
