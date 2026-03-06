import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import { HelmetProvider } from "react-helmet-async";
import Navbar from "./components/Navbar";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
};

// Pages
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import JoinPage from "./pages/JoinPage";
import BetaSignupPage from "./pages/BetaSignupPage";
import HivePage from "./pages/HivePage";
import ExplorePage from "./pages/ExplorePage";
import CollectionPage from "./pages/CollectionPage";
import AddRecordPage from "./pages/AddRecordPage";
import ProfilePage from "./pages/ProfilePage";
import RecordDetailPage from "./pages/RecordDetailPage";
import SettingsPage from "./pages/SettingsPage";
import CreateHaulPage from "./pages/CreateHaulPage";
import ISOPage from "./pages/ISOPage";
import TradesPage from "./pages/TradesPage";
import AdminDisputesPage from "./pages/AdminDisputesPage";
import AdminPage from "./pages/AdminPage";
import MessagesPage from "./pages/MessagesPage";
import FAQPage from "./pages/FAQPage";
import AboutPage from "./pages/AboutPage";
import TermsPage from "./pages/TermsPage";
import PrivacyPage from "./pages/PrivacyPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ExploreSeeAllPage from "./pages/ExploreSeeAllPage";
import WaxReportPage from "./pages/WaxReportPage";
import WaxReportHistory from "./pages/WaxReportHistory";

// Auth guards
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/" replace />;
  return children;
};

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/" replace />;
  if (!user.is_admin) return <Navigate to="/hive" replace />;
  return children;
};

const LoadingScreen = () => (
  <div className="min-h-screen bg-[#FAF6EE] flex flex-col items-center justify-center">
    <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-10 mb-8" />
    <svg width="140" height="180" viewBox="0 0 140 180" fill="none" className="overflow-visible">
      <path d="M25 55 C25 55 15 65 12 90 C9 115 12 145 20 158 C28 170 40 175 70 175 C100 175 112 170 120 158 C128 145 131 115 128 90 C125 65 115 55 115 55 Z" fill="#FAF6EE" stroke="#C8861A" strokeWidth="3" strokeOpacity="0.3"/>
      <clipPath id="jar-clip-r">
        <path d="M25 55 C25 55 15 65 12 90 C9 115 12 145 20 158 C28 170 40 175 70 175 C100 175 112 170 120 158 C128 145 131 115 128 90 C125 65 115 55 115 55 Z"/>
      </clipPath>
      <g clipPath="url(#jar-clip-r)">
        <rect x="0" y="180" width="140" height="140" fill="url(#honey-grad-r)" className="animate-jar-fill"/>
      </g>
      <defs>
        <linearGradient id="honey-grad-r" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#E8A820"/>
          <stop offset="100%" stopColor="#C8861A"/>
        </linearGradient>
      </defs>
      <path d="M30 55 L30 42 C30 38 35 35 40 35 L100 35 C105 35 110 38 110 42 L110 55" fill="#FAF6EE" stroke="#C8861A" strokeWidth="3" strokeOpacity="0.3"/>
      <rect x="28" y="28" width="84" height="10" rx="4" fill="#FAF6EE" stroke="#C8861A" strokeWidth="3" strokeOpacity="0.3"/>
      <path d="M28 55 C28 55 22 58 20 70 C19 76 22 78 25 75 C27 73 28 65 28 55 Z" fill="#E8A820" opacity="0.6"/>
    </svg>
    <p className="mt-6 text-[#8A6B4A] text-base italic" style={{ fontFamily: "'Cormorant Garamond', Georgia, serif" }}>filling the hive...</p>
  </div>
);

// App Layout with Navbar
const AppLayout = ({ children }) => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-honey-cream relative">
      {user && <Navbar />}
      <main className="relative z-10">
        {children}
      </main>
    </div>
  );
};

// Landing wrapper - redirects to hive if logged in
const LandingWrapper = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-honey-cream flex items-center justify-center">
        <div className="w-12 h-12 bg-honey rounded-full animate-pulse"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/hive" replace />;
  }

  return <LandingPage />;
};

function AppContent() {
  return (
    <Routes>
      {/* Public routes — no auth required */}
      <Route path="/" element={<LandingWrapper />} />
      <Route path="/beta" element={<BetaSignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/join" element={<JoinPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/faq" element={<FAQPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      {/* Protected routes — auth required */}
      <Route path="/explore" element={
        <ProtectedRoute>
          <AppLayout><ExplorePage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/explore/:section" element={
        <ProtectedRoute>
          <AppLayout><ExploreSeeAllPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/hive" element={
        <ProtectedRoute>
          <AppLayout><HivePage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/collection" element={
        <ProtectedRoute>
          <AppLayout><CollectionPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/add-record" element={
        <ProtectedRoute>
          <AppLayout><AddRecordPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/create-haul" element={
        <ProtectedRoute>
          <AppLayout><CreateHaulPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/honeypot" element={
        <ProtectedRoute>
          <AppLayout><ISOPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/honeypot/listing/:listingId" element={
        <ProtectedRoute>
          <AppLayout><ISOPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/iso" element={<Navigate to="/honeypot" replace />} />
      <Route path="/trades" element={
        <ProtectedRoute>
          <AppLayout><TradesPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/messages" element={
        <ProtectedRoute>
          <AppLayout><MessagesPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout><SettingsPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/wax-reports" element={
        <ProtectedRoute>
          <AppLayout><WaxReportPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/wax-reports/history" element={
        <ProtectedRoute>
          <AppLayout><WaxReportHistory /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/wax-reports/:reportId" element={
        <ProtectedRoute>
          <AppLayout><WaxReportPage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/profile/:username" element={
        <ProtectedRoute>
          <AppLayout><ProfilePage /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/record/:recordId" element={
        <ProtectedRoute>
          <AppLayout><RecordDetailPage /></AppLayout>
        </ProtectedRoute>
      } />

      {/* Admin routes */}
      <Route path="/admin" element={
        <AdminRoute>
          <AppLayout><AdminPage /></AppLayout>
        </AdminRoute>
      } />
      <Route path="/admin/disputes" element={
        <AdminRoute>
          <AppLayout><AdminDisputesPage /></AppLayout>
        </AdminRoute>
      } />
      <Route path="/admin/beta" element={<Navigate to="/admin?section=beta" replace />} />

      {/* Catch all — redirect to landing */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  useEffect(() => {
    const loader = document.getElementById('loading-screen');
    if (loader) {
      loader.style.opacity = '0';
      setTimeout(() => loader.remove(), 400);
    }
  }, []);

  return (
    <HelmetProvider>
      <BrowserRouter>
        <ScrollToTop />
        <AuthProvider>
          <AppContent />
          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
