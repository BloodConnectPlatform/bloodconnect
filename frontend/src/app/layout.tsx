import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { AuthModal } from '@/components/auth/AuthModal';
import { PlatformNoticeModal } from '@/components/common/PlatformNoticeModal';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Blood Connect — Connecting Donors. Reaching Those in Need.',
  description:
    'A community-driven blood donor discovery platform connecting voluntary donors with patients in urgent medical need across Coimbatore. Safe, fast, and privacy-first.',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
    apple: '/apple-icon.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-full flex flex-col bg-slate-50 text-slate-900 antialiased`}>
        <AuthProvider>
          <PlatformNoticeModal />
          <Navbar />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
          <AuthModal />
        </AuthProvider>
      </body>
    </html>
  );
}
