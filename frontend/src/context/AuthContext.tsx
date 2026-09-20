'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, DonorProfile } from '@/types';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  donorProfile: DonorProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isLoginModalOpen: boolean;
  openLoginModal: () => void;
  closeLoginModal: () => void;
  login: (mobileNumber: string, otpCode: string) => Promise<User>;
  authenticateRequester: (name: string, mobileNumber: string, otpCode: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setDonorProfile: (profile: DonorProfile | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [donorProfile, setDonorProfile] = useState<DonorProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const openLoginModal = useCallback(() => setIsLoginModalOpen(true), []);
  const closeLoginModal = useCallback(() => setIsLoginModalOpen(false), []);

  const refreshUser = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setUser(null);
      setDonorProfile(null);
      setIsLoading(false);
      return;
    }

    try {
      const me = await api.getMe();
      setUser(me);
      if (me.role === 'DONOR') {
        try {
          const profile = await api.getDonorProfile();
          setDonorProfile(profile);
        } catch {
          // No donor profile yet or incomplete
        }
      }
    } catch {
      api.clearTokens();
      setUser(null);
      setDonorProfile(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (mobileNumber: string, otpCode: string): Promise<User> => {
    const authData = await api.login(mobileNumber, otpCode);
    setUser(authData.user);
    if (authData.user.role === 'DONOR') {
      try {
        const profile = await api.getDonorProfile();
        setDonorProfile(profile);
      } catch {
        // Profile not found
      }
    }
    closeLoginModal();
    return authData.user;
  };

  const authenticateRequester = async (
    name: string,
    mobileNumber: string,
    otpCode: string
  ): Promise<User> => {
    const authData = await api.authenticateRequester({
      name,
      mobile_number: mobileNumber,
      otp_code: otpCode,
    });
    setUser(authData.user);
    if (authData.user.role === 'DONOR') {
      try {
        const profile = await api.getDonorProfile();
        setDonorProfile(profile);
      } catch {
        // Profile not found
      }
    }
    closeLoginModal();
    return authData.user;
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      api.clearTokens();
      setUser(null);
      setDonorProfile(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('bloodconnect_last_patient');
        window.location.href = '/';
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        donorProfile,
        isAuthenticated: !!user,
        isLoading,
        isLoginModalOpen,
        openLoginModal,
        closeLoginModal,
        login,
        authenticateRequester,
        logout,
        refreshUser,
        setDonorProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
