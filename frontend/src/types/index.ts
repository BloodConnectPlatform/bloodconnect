export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-';
export type UserRole = 'DONOR' | 'REQUESTER' | 'ADMIN';
export type RequestStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED' | 'FULFILLED';
export type UrgencyLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ReportReason =
  | 'INCORRECT_INFORMATION'
  | 'FAKE_PROFILE'
  | 'WRONG_BLOOD_GROUP'
  | 'SPAM'
  | 'MISUSE'
  | 'OTHER';
export type ReportStatus = 'OPEN' | 'REVIEWING' | 'RESOLVED' | 'DISMISSED';
export type NotificationType = 'REQUEST_RECEIVED' | 'REQUEST_ACCEPTED' | 'REQUEST_REJECTED' | 'REPORT' | 'SYSTEM';
export type Gender = 'MALE' | 'FEMALE' | 'OTHER';

export interface LocationItem {
  id: number;
  name: string;
  district: string;
  state?: string;
  is_active?: boolean;
}

export interface User {
  id: string | number;
  name?: string;
  mobile_number?: string;
  mobile?: string;
  role: UserRole;
  is_active: boolean;
  is_verified?: boolean;
  has_donor_profile?: boolean;
  created_at: string;
}

export interface DonorProfile {
  id: string | number;
  user_id: string | number;
  full_name?: string;
  name?: string;
  mobile?: string;
  blood_group: BloodGroup;
  gender?: Gender;
  date_of_birth: string;
  age?: number;
  location_id?: number;
  is_available: boolean;
  is_active?: boolean;
  is_otp_verified?: boolean;
  contact_consent?: boolean;
  last_donated_at?: string;
  total_donations?: number;
  reports_count?: number;
  created_at: string;
  updated_at?: string;
  location: LocationItem;
  user?: User;
}

export interface PublicDonor {
  id: string | number;
  name?: string;
  full_name?: string;
  blood_group: BloodGroup;
  gender?: Gender;
  age?: number;
  date_of_birth?: string;
  location: LocationItem;
  is_available: boolean;
  last_donated_at?: string;
  total_donations?: number;
  created_at?: string;
}

export interface BloodRequest {
  id: string | number;
  requester_id?: string | number;
  donor_id?: string | number;
  blood_group?: BloodGroup;
  location?: LocationItem;
  patient_name?: string;
  hospital_name?: string;
  required_units?: number;
  urgency?: UrgencyLevel;
  message?: string;
  status: RequestStatus;
  created_at: string;
  updated_at?: string;
  responded_at?: string;
  // Disclosed strictly when status is ACCEPTED
  donor_name?: string;
  donor_mobile?: string;
  donor_contact?: string;
  requester_name?: string;
  requester_mobile?: string;
  requester_contact?: string;
  donor?: PublicDonor;
  requester?: {
    id?: string | number;
    name?: string;
    mobile_number?: string;
    mobile?: string;
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
  total_registered_donors?: number;
  total_donors?: number;
  total_users?: number;
  available_donors: number;
  active_donors?: number;
  verified_donors?: number;
  requests?: {
    pending: number;
    accepted: number;
    rejected: number;
    total: number;
  };
  reports?: {
    open: number;
    reviewing: number;
    resolved: number;
    dismissed: number;
    total: number;
  };
  total_requests?: number;
  pending_requests?: number;
  accepted_requests?: number;
  total_reports?: number;
  pending_reports?: number;
  donors_by_blood_group?: Record<string, number>;
  donors_by_location?: Record<string, number>;
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
