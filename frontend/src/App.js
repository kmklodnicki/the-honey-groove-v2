import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import { HelmetProvider } from "react-helmet-async";
import Navbar from "./components/Navbar";

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
  <div className="min-h-screen bg-honey-cream flex items-center justify-center">
    <div className="text-center">
      <div className="w-12 h-12 bg-honey rounded-full animate-pulse mx-auto mb-4"></div>
      <p className="text-muted-foreground">Loading...</p>
    </div>
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
      <Route path="/iso" element={<Navigate to="/honeypot" replace />} />
      <Route path="/trades" element={<Navigate to="/honeypot" replace />} />
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
        <AuthProvider>
          <AppContent />
          <Toaster position="top-center" richColors />
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
