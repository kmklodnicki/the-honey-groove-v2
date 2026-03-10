import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { VariantModalProvider } from "./context/VariantModalContext";
import VariantModal from "./components/VariantModal";
import { Toaster } from "./components/ui/sonner";
import { HelmetProvider } from "react-helmet-async";
import { ArrowLeft } from "lucide-react";
import Navbar from "./components/Navbar";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
    // iOS Safari fix: clean up stale scroll locks left by Radix UI dialogs/sheets
    // When navigating while a modal is open, the cleanup can fail, leaving body frozen
    const body = document.body;
    if (body.hasAttribute('data-scroll-locked')) {
      body.removeAttribute('data-scroll-locked');
    }
    body.style.overflow = '';
    body.style.paddingRight = '';
    body.style.position = '';
    body.style.top = '';
    body.style.left = '';
    body.style.right = '';
    body.style.width = '';
    // Also clean html element (some scroll-lock libs target both)
    const html = document.documentElement;
    html.style.overflow = '';
  }, [pathname]);
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
import StripeConnectReturnPage from "./pages/StripeConnectReturnPage";
import StripeConnectRefreshPage from "./pages/StripeConnectRefreshPage";
import OrdersPage from "./pages/OrdersPage";
import ConfirmEmailChangePage from "./pages/ConfirmEmailChangePage";
import WelcomeHivePage from "./pages/WelcomeHivePage";
import EssentialsPage from "./pages/EssentialsPage";
import VinylVariantPage from "./pages/VinylVariantPage";
import SearchPage from "./pages/SearchPage";

// Auth guards — loading is ALWAYS false. No gates.
// If user exists (from JWT decode or login), render children.
// If no user, redirect to login.
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" replace />;
  return children;
};

// Admin route waits for full user data (JWT-decoded user won't have is_admin)
const AdminRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" replace />;
  // If we only have JWT-decoded partial user, wait for background fetch
  if (user._fromToken) return <div className="min-h-screen bg-honey-cream" />;
  if (!user.is_admin) return <Navigate to="/hive" replace />;
  return children;
};

// App Layout with Navbar
const AppLayout = ({ children }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isHome = location.pathname === '/' || location.pathname === '/hive';
  // Pages with their own inline back button don't need the global floating one
  const hasInlineBack = location.pathname.startsWith('/record/') || location.pathname.startsWith('/vinyl/');
  
  return (
    <div className="min-h-screen relative" style={{ background: 'transparent' }}>
      {user && <Navbar />}
      {user && !isHome && !hasInlineBack && (
        <button
          onClick={() => navigate(-1)}
          className="fixed z-40 flex items-center justify-center w-8 h-8 rounded-full text-stone-400/70 hover:text-stone-600 hover:bg-stone-200/40 transition-all top-[56px] md:top-[94px] left-3 md:left-5"
          data-testid="global-back-btn"
          aria-label="Go back"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
      )}
      <main className="relative z-10">
        {children}
      </main>
    </div>
  );
};

// Landing wrapper - redirects to hive if logged in
const LandingWrapper = () => {
  const { user } = useAuth();
  if (user) return <Navigate to="/hive" replace />;
  return <LandingPage />;
};

// Invite redirect — /invite/:code → /join?code=:code
const InviteRedirect = () => {
  const { code } = useParams();
  return <Navigate to={`/join?code=${code}`} replace />;
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
      <Route path="/invite/:code" element={<InviteRedirect />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/faq" element={<FAQPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/confirm-email-change" element={<ConfirmEmailChangePage />} />
      <Route path="/stripe/connect/return" element={<StripeConnectReturnPage />} />
      <Route path="/stripe/connect/refresh" element={<StripeConnectRefreshPage />} />

      {/* Public vinyl variant SEO pages */}
      <Route path="/vinyl/:artist/:album/:variant" element={<AppLayout><VinylVariantPage /></AppLayout>} />

      {/* Full search page */}
      <Route path="/search" element={<AppLayout><SearchPage /></AppLayout>} />

      {/* Protected routes */}
      <Route path="/onboarding/welcome-to-the-hive" element={<ProtectedRoute><WelcomeHivePage /></ProtectedRoute>} />
      <Route path="/nectar" element={<ProtectedRoute><AppLayout><ExplorePage /></AppLayout></ProtectedRoute>} />
      <Route path="/nectar/:section" element={<ProtectedRoute><AppLayout><ExploreSeeAllPage /></AppLayout></ProtectedRoute>} />
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
      <Route path="/orders" element={<ProtectedRoute><AppLayout><OrdersPage /></AppLayout></ProtectedRoute>} />
      <Route path="/essentials" element={<ProtectedRoute><AppLayout><EssentialsPage /></AppLayout></ProtectedRoute>} />
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
  console.log('APP RENDERING');
  useEffect(() => {
    console.log('APP MOUNTED');
    // Remove the static HTML loading screen immediately on mount
    const loader = document.getElementById('loading-screen');
    if (loader) loader.remove();
    // Also remove the fallback screen since the app mounted successfully
    const fallback = document.getElementById('safari-fallback');
    if (fallback) fallback.remove();

    // iOS Safari scroll-freeze safety net:
    // Clean up orphaned scroll locks on visibility change (tab switch back)
    // and periodically check for stale locks with no visible overlay
    const cleanScrollLock = () => {
      const body = document.body;
      if (body.hasAttribute('data-scroll-locked')) {
        // Only clean if no Radix overlay is actually visible
        const hasOverlay = document.querySelector('[data-radix-focus-guard], [role="dialog"], [data-state="open"]');
        if (!hasOverlay) {
          body.removeAttribute('data-scroll-locked');
          body.style.overflow = '';
          body.style.paddingRight = '';
          body.style.position = '';
          body.style.top = '';
          body.style.left = '';
          body.style.right = '';
          body.style.width = '';
          document.documentElement.style.overflow = '';
        }
      }
    };

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') cleanScrollLock();
    });

    // Check every 3s for stale locks (cheap DOM check, no-op if lock is absent)
    const interval = setInterval(cleanScrollLock, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <HelmetProvider>
      <BrowserRouter>
        <ScrollToTop />
        <AuthProvider>
          <VariantModalProvider>
            <AppContent />
            <VariantModal />
            <Toaster />
          </VariantModalProvider>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
