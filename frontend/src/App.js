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

// Auth guards — NO loading gate. Render immediately or redirect.
// If auth is still loading, we render null (transparent) instead of a blocking screen.
// The index.html fallback handles the visual gap.
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  return children;
};

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  if (!user.is_admin) return <Navigate to="/hive" replace />;
  return children;
};

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
  if (loading) return null;
  if (user) return <Navigate to="/hive" replace />;
  return <LandingPage />;
};

function AppContent() {
  // Debug: confirm React app is mounting (Safari diagnostic)
  useEffect(() => {
    console.log('app mounted');
  }, []);

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingWrapper />} />
      <Route path="/beta" element={<BetaSignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/join" element={<JoinPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/faq" element={<FAQPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      {/* Protected routes */}
      <Route path="/explore" element={<ProtectedRoute><AppLayout><ExplorePage /></AppLayout></ProtectedRoute>} />
      <Route path="/explore/:section" element={<ProtectedRoute><AppLayout><ExploreSeeAllPage /></AppLayout></ProtectedRoute>} />
      <Route path="/hive" element={<ProtectedRoute><AppLayout><HivePage /></AppLayout></ProtectedRoute>} />
      <Route path="/collection" element={<ProtectedRoute><AppLayout><CollectionPage /></AppLayout></ProtectedRoute>} />
      <Route path="/add-record" element={<ProtectedRoute><AppLayout><AddRecordPage /></AppLayout></ProtectedRoute>} />
      <Route path="/create-haul" element={<ProtectedRoute><AppLayout><CreateHaulPage /></AppLayout></ProtectedRoute>} />
      <Route path="/honeypot" element={<ProtectedRoute><AppLayout><ISOPage /></AppLayout></ProtectedRoute>} />
      <Route path="/honeypot/listing/:listingId" element={<ProtectedRoute><AppLayout><ISOPage /></AppLayout></ProtectedRoute>} />
      <Route path="/iso" element={<Navigate to="/honeypot" replace />} />
      <Route path="/trades" element={<ProtectedRoute><AppLayout><TradesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/messages" element={<ProtectedRoute><AppLayout><MessagesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports" element={<ProtectedRoute><AppLayout><WaxReportPage /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports/history" element={<ProtectedRoute><AppLayout><WaxReportHistory /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports/:reportId" element={<ProtectedRoute><AppLayout><WaxReportPage /></AppLayout></ProtectedRoute>} />
      <Route path="/profile/:username" element={<ProtectedRoute><AppLayout><ProfilePage /></AppLayout></ProtectedRoute>} />
      <Route path="/record/:recordId" element={<ProtectedRoute><AppLayout><RecordDetailPage /></AppLayout></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin" element={<AdminRoute><AppLayout><AdminPage /></AppLayout></AdminRoute>} />
      <Route path="/admin/disputes" element={<AdminRoute><AppLayout><AdminDisputesPage /></AppLayout></AdminRoute>} />
      <Route path="/admin/beta" element={<Navigate to="/admin?section=beta" replace />} />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  useEffect(() => {
    // Remove the static HTML loading screen immediately on mount
    const loader = document.getElementById('loading-screen');
    if (loader) loader.remove();
    // Also remove the fallback screen since the app mounted successfully
    const fallback = document.getElementById('safari-fallback');
    if (fallback) fallback.remove();
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
