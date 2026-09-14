import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { MedicalDisclaimer } from '@/components/common/MedicalDisclaimer';
import { AuthModal } from '@/components/auth/AuthModal';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Blood Connect — Voluntary Blood Donor Discovery Network (Tamil Nadu)',
  description:
    'A community-driven blood donor discovery platform connecting voluntary donors with patients in urgent medical need across Tamil Nadu. Safe, fast, and privacy-first.',
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
          <MedicalDisclaimer variant="banner" />
          <Navbar />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
          <AuthModal />
        </AuthProvider>
      </body>
    </html>
  );
}
