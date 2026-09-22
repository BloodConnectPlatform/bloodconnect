import {
  AdminStats,
  AuthTokens,
  BloodGroup,
  BloodRequest,
  DonorProfile,
  LocationItem,
  NotificationItem,
  PaginatedResponse,
  PublicDonor,
  PublicStats,
  LegalDocument,
  ReportItem,
  ReportReason,
  ReportStatus,
  UrgencyLevel,
  User,
} from '@/types';

function getApiBaseUrl(): string {
  let url = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (url) {
    url = url.replace(/\/+$/, '');
    if (!url.endsWith('/api/v1')) {
      url = `${url}/api/v1`;
    }
    return url;
  }
  return typeof window !== 'undefined'
    ? '/api/v1'
    : (process.env.INTERNAL_API_URL ? `${process.env.INTERNAL_API_URL.replace(/\/+$/, '')}/api/v1` : 'http://127.0.0.1:8000/api/v1');
}

const API_BASE_URL = getApiBaseUrl();


class ApiClient {
  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private setTokens(access_token: string, refresh_token: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
  }

  public clearTokens() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('bloodconnect_user');
    localStorage.removeItem('bloodconnect_last_patient');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${API_BASE_URL}${endpoint}`;
    let response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token refresh if 401 Unauthorized
    if (response.status === 401 && typeof window !== 'undefined') {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
        try {
          const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const data: AuthTokens = await refreshRes.json();
            this.setTokens(data.access_token, data.refresh_token);
            headers['Authorization'] = `Bearer ${data.access_token}`;
            response = await fetch(url, {
              ...options,
              headers,
            });
          } else {
            this.clearTokens();
          }
        } catch {
          this.clearTokens();
        }
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message =
        errorData.detail ||
        (Array.isArray(errorData) ? errorData.map((e: any) => e.msg).join(', ') : 'An unexpected error occurred');
      throw new Error(message);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // ===================== AUTH =====================
  async sendOtp(mobile_number: string, purpose: 'LOGIN' | 'DONOR_REGISTRATION' | 'REQUESTER_VERIFICATION' = 'LOGIN') {
    return this.request<{ message: string; cooldown_seconds: number; expires_in_seconds: number; debug_otp?: string }>(
      '/auth/send-otp',
      {
        method: 'POST',
        body: JSON.stringify({ mobile: mobile_number, purpose }),
      }
    );
  }

  async verifyOtp(mobile_number: string, otp_code: string) {
    return this.request<{ message: string; verified: boolean; verification_token: string; is_registered: boolean; role?: string }>(
      '/auth/verify-otp',
      {
        method: 'POST',
        body: JSON.stringify({ mobile: mobile_number, otp: otp_code }),
      }
    );
  }

  async login(mobile_number: string, otp_code: string) {
    const res = await this.request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ mobile: mobile_number, otp: otp_code }),
    });
    this.setTokens(res.access_token, res.refresh_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('bloodconnect_user', JSON.stringify(res.user));
    }
    return res;
  }

  async authenticateRequester(data: { name: string; mobile_number: string; otp_code: string }) {
    const res = await this.request<AuthTokens>('/auth/requester-auth', {
      method: 'POST',
      body: JSON.stringify({
        name: data.name,
        mobile: data.mobile_number,
        otp: data.otp_code,
      }),
    });
    this.setTokens(res.access_token, res.refresh_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('bloodconnect_user', JSON.stringify(res.user));
    }
    return res;
  }

  async redeemWhatsAppToken(token: string) {
    const res = await this.request<AuthTokens>('/auth/whatsapp/redeem', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
    this.setTokens(res.access_token, res.refresh_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('bloodconnect_user', JSON.stringify(res.user));
    }
    return res;
  }

  async getMe() {
    return this.request<User>('/auth/me');
  }

  async logout() {
    try {
      await this.request<{ message: string }>('/auth/logout', { method: 'POST' });
    } finally {
      this.clearTokens();
    }
  }

  // ===================== LOCATIONS =====================
  async getLocations() {
    return this.request<LocationItem[]>('/locations');
  }

  // ===================== DONORS & SEARCH =====================
  async registerDonor(data: {
    mobile_number: string;
    verification_token: string;
    full_name: string;
    blood_group: BloodGroup;
    gender: string;
    date_of_birth: string;
    location_id: number;
    is_available?: boolean;
    last_donated_at?: string;
  }) {
    const res = await this.request<AuthTokens>('/donors', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setTokens(res.access_token, res.refresh_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('bloodconnect_user', JSON.stringify(res.user));
    }
    return res;
  }

  async getDonorProfile() {
    return this.request<DonorProfile>('/donors/me');
  }

  async updateDonorProfile(data: {
    full_name?: string;
    location_id?: number;
    last_donated_at?: string | null;
  }) {
    return this.request<DonorProfile>('/donors/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async toggleAvailability(is_available: boolean) {
    return this.request<DonorProfile>('/donors/availability', {
      method: 'PATCH',
      body: JSON.stringify({ is_available }),
    });
  }

  async getDonorDashboard() {
    return this.request<{
      profile: DonorProfile;
      pending_requests: BloodRequest[];
      accepted_requests: BloodRequest[];
      recent_requests: BloodRequest[];
    }>('/donors/dashboard');
  }

  async searchDonors(params: {
    blood_group?: BloodGroup;
    location_id?: number;
    location?: string;
    district?: string;
    page?: number;
    page_size?: number;
  }) {
    const query = new URLSearchParams();
    if (params.blood_group) query.append('blood_group', params.blood_group);
    if (params.location_id) query.append('location_id', params.location_id.toString());
    if (params.location) query.append('location', params.location);
    if (params.district) query.append('district', params.district);
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<PublicDonor>>(`/donors/search?${query.toString()}`);
  }

  async getPublicStats() {
    return this.request<PublicStats>('/donors/public-stats');
  }

  // ===================== LEGAL & COMPLIANCE =====================
  async getPrivacyPolicy() {
    return this.request<LegalDocument>('/privacy-policy');
  }

  async getTerms() {
    return this.request<LegalDocument>('/terms');
  }

  async getDataDeletionInstructions() {
    return this.request<LegalDocument>('/data-deletion');
  }

  // ===================== BLOOD REQUESTS =====================
  async createRequest(data: {
    donor_id: string | number;
    patient_name?: string;
    hospital_name?: string;
    required_units?: number;
    urgency?: UrgencyLevel;
    message?: string;
    blood_group?: BloodGroup;
    location_id?: number;
  }) {
    return this.request<BloodRequest>('/requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMySentRequests(page = 1, page_size = 20) {
    return this.request<PaginatedResponse<BloodRequest>>(
      `/requests/sent?page=${page}&page_size=${page_size}`
    );
  }

  async getRequestDetails(requestId: string | number) {
    return this.request<BloodRequest>(`/requests/${requestId}`);
  }

  async acceptRequest(requestId: string | number) {
    return this.request<BloodRequest>(`/requests/${requestId}/accept`, {
      method: 'POST',
    });
  }

  async rejectRequest(requestId: string | number) {
    return this.request<BloodRequest>(`/requests/${requestId}/reject`, {
      method: 'POST',
    });
  }

  async deleteRequest(requestId: string | number) {
    return this.request<{ success: boolean; message: string }>(`/requests/${requestId}`, {
      method: 'DELETE',
    });
  }

  // ===================== NOTIFICATIONS =====================
  async getNotifications(page = 1, page_size = 20) {
    return this.request<PaginatedResponse<NotificationItem>>(
      `/notifications?page=${page}&page_size=${page_size}`
    );
  }

  async markNotificationRead(notificationId: string | number) {
    return this.request<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  }

  async markAllNotificationsRead() {
    return this.request<{ message: string; count: number }>('/notifications/read-all', {
      method: 'POST',
    });
  }

  // ===================== REPORTS =====================
  async createReport(data: {
    donor_id: string | number;
    reason: ReportReason;
    description?: string;
  }) {
    return this.request<ReportItem>('/reports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ===================== ADMIN =====================
  async getAdminStats() {
    return this.request<AdminStats>('/admin/statistics');
  }

  async listAdminDonors(params?: {
    blood_group?: BloodGroup;
    location_id?: number;
    is_active?: boolean;
    is_available?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }) {
    const query = new URLSearchParams();
    if (params?.blood_group) query.append('blood_group', params.blood_group);
    if (params?.location_id) query.append('location_id', params.location_id.toString());
    if (params?.is_active !== undefined) query.append('is_active', params.is_active.toString());
    if (params?.is_available !== undefined) query.append('is_available', params.is_available.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<DonorProfile>>(`/admin/donors?${query.toString()}`);
  }

  async toggleDonorStatus(donorId: string | number, is_active: boolean, reason?: string) {
    const action = is_active ? 'activate' : 'deactivate';
    return this.request<DonorProfile>(`/admin/donors/${donorId}/${action}`, {
      method: 'PATCH',
    });
  }

  async toggleDonorAvailabilityAdmin(donorId: string | number, is_available: boolean, reason?: string) {
    return this.request<DonorProfile>(`/admin/donors/${donorId}/availability`, {
      method: 'PATCH',
      body: JSON.stringify({ is_available }),
    });
  }

  async deleteDonorAdmin(donorId: string | number, reason?: string) {
    return this.request<{ message: string; data?: any }>(`/admin/donors/${donorId}`, {
      method: 'DELETE',
    });
  }

  async listAdminRequests(page = 1, page_size = 20) {
    return this.request<PaginatedResponse<BloodRequest>>(`/admin/requests?page=${page}&page_size=${page_size}`);
  }

  async listAdminReports(params?: { status?: ReportStatus; page?: number; page_size?: number }) {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<ReportItem>>(`/admin/reports?${query.toString()}`);
  }

  async handleAdminReport(reportId: string | number, status: ReportStatus, resolution_notes?: string) {
    return this.request<ReportItem>(`/admin/reports/${reportId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes: resolution_notes || undefined }),
    });
  }

  async getAdminAuditLogs(page = 1, page_size = 20) {
    return this.request<PaginatedResponse<any>>(`/admin/audit-logs?page=${page}&page_size=${page_size}`);
  }

  async manageAdmins(data: {
    action: 'PROMOTE' | 'DEMOTE' | 'UPDATE_NAME' | 'LIST';
    mobile?: string;
    name?: string;
    user_id?: string;
  }) {
    return this.request<{
      success: boolean;
      message: string;
      action: 'PROMOTE' | 'DEMOTE' | 'UPDATE_NAME' | 'LIST';
      user?: {
        id: string;
        name: string;
        mobile: string;
        role: string;
        is_active: boolean;
        created_at?: string;
      };
      admins?: Array<{
        id: string;
        name: string;
        mobile: string;
        role: string;
        is_active: boolean;
        created_at?: string;
      }>;
    }>('/admin/manage-admins', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();

