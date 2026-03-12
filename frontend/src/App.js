import React, { useEffect, useState, Suspense, lazy } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { VariantModalProvider } from "./context/VariantModalContext";
import { SocketProvider } from "./context/SocketContext";
import VariantModal from "./components/VariantModal";
import { Toaster } from "./components/ui/sonner";
import { HelmetProvider } from "react-helmet-async";
import { SWRConfig } from "swr";
import { ArrowLeft, Shield, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import Navbar from "./components/Navbar";
import DiscogsSecurityModal from "./components/DiscogsSecurityModal";

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

// Pages — critical path (eager)
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import JoinPage from "./pages/JoinPage";
import HivePage from "./pages/HivePage";

// Pages — below-fold (lazy loaded)
const BetaSignupPage = lazy(() => import("./pages/BetaSignupPage"));
const ExplorePage = lazy(() => import("./pages/ExplorePage"));
const CollectionPage = lazy(() => import("./pages/CollectionPage"));
const AddRecordPage = lazy(() => import("./pages/AddRecordPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const RecordDetailPage = lazy(() => import("./pages/RecordDetailPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const CreateHaulPage = lazy(() => import("./pages/CreateHaulPage"));
const ISOPage = lazy(() => import("./pages/ISOPage"));
const TradesPage = lazy(() => import("./pages/TradesPage"));
const AdminDisputesPage = lazy(() => import("./pages/AdminDisputesPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const MessagesPage = lazy(() => import("./pages/MessagesPage"));
const FAQPage = lazy(() => import("./pages/FAQPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const TermsPage = lazy(() => import("./pages/TermsPage"));
const PrivacyPage = lazy(() => import("./pages/PrivacyPage"));
const VerifyEmailPage = lazy(() => import("./pages/VerifyEmailPage"));
const ExploreSeeAllPage = lazy(() => import("./pages/ExploreSeeAllPage"));
const WaxReportPage = lazy(() => import("./pages/WaxReportPage"));
const WaxReportHistory = lazy(() => import("./pages/WaxReportHistory"));
const WeeklyReportPage = lazy(() => import("./pages/WeeklyReportPage"));
const StripeConnectReturnPage = lazy(() => import("./pages/StripeConnectReturnPage"));
const StripeConnectRefreshPage = lazy(() => import("./pages/StripeConnectRefreshPage"));
const OrdersPage = lazy(() => import("./pages/OrdersPage"));
const ConfirmEmailChangePage = lazy(() => import("./pages/ConfirmEmailChangePage"));
const WelcomeHivePage = lazy(() => import("./pages/WelcomeHivePage"));
const EssentialsPage = lazy(() => import("./pages/EssentialsPage"));
const VinylVariantPage = lazy(() => import("./pages/VinylVariantPage"));
const VariantReleasePage = lazy(() => import("./pages/VariantReleasePage"));
const SearchPage = lazy(() => import("./pages/SearchPage"));
const CheckoutSuccessPage = lazy(() => import("./pages/CheckoutSuccessPage"));

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

// Route key wrappers — force full re-mount when URL params change (prevents "ghosting")
const VinylVariantPageWrapper = () => {
  const { artist, album, variant } = useParams();
  return <VinylVariantPage key={`${artist}/${album}/${variant}`} />;
};
const VariantReleasePageWrapper = () => {
  const { releaseId } = useParams();
  return <VariantReleasePage key={releaseId} />;
};

// App Layout with Navbar
const AppLayout = ({ children }) => {
  const { user, token, API, updateUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showMigration, setShowMigration] = useState(false);

  // BLOCK 585/587: Conditional banner logic based on discogs_import_intent
  const [oauthLoading, setOAuthLoading] = useState(false);

  // BLOCK 587: Banner shows only for LATER intent (or legacy PENDING users who dismissed migration)
  const intentShowsBanner = () => {
    if (!user || user.discogs_oauth_verified) return false;
    const intent = user.discogs_import_intent || 'PENDING';
    if (intent === 'DECLINED' || intent === 'CONNECTED') return false;
    if (intent === 'LATER') return true;
    // Legacy: PENDING users who already dismissed migration modal → treat as LATER
    if (intent === 'PENDING' && user.discogs_migration_dismissed) return true;
    return false;
  };

  // BLOCK 585: 24h skip via localStorage
  const isSkippedRecently = () => {
    try {
      const ts = localStorage.getItem('honeygroove_discogs_skip_ts');
      if (!ts) return false;
      return Date.now() - parseInt(ts, 10) < 24 * 60 * 60 * 1000;
    } catch { return false; }
  };

  const [skippedLocal, setSkippedLocal] = useState(isSkippedRecently);
  const showOAuthBanner = intentShowsBanner() && !skippedLocal;

  // BLOCK 583: User-initiated OAuth launch — must be direct onClick, not auto-popup
  const handleOAuthClick = async () => {
    setOAuthLoading(true);
    try {
      const origin = window.location.origin;
      localStorage.setItem('honeygroove_oauth_pending', JSON.stringify({ user_id: user?.id, ts: Date.now() }));
      const resp = await axios.get(`${API}/discogs/oauth/start?frontend_origin=${origin}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const authUrl = resp.data?.auth_url;
      if (!authUrl) {
        toast.error('Discogs OAuth is not configured. Contact support.');
        setOAuthLoading(false);
        return;
      }
      window.location.href = authUrl;
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Could not start Discogs connection. Try again.';
      toast.error(msg);
      setOAuthLoading(false);
    }
  };

  // BLOCK 585: "Skip for now" — hides banner for 24 hours via localStorage
  const handleSkipBanner = () => {
    localStorage.setItem('honeygroove_discogs_skip_ts', Date.now().toString());
    setSkippedLocal(true);
  };

  // BLOCK 583: On return from OAuth, check localStorage and trigger Gold Shield
  useEffect(() => {
    const pending = localStorage.getItem('honeygroove_oauth_pending');
    if (pending && user?.discogs_oauth_verified) {
      localStorage.removeItem('honeygroove_oauth_pending');
    }
  }, [user]);

  // BLOCK 492: Mount migration modal immediately after session loads
  // Trigger: user.needs_discogs_migration (computed from has_seen_security_migration === false)
  useEffect(() => {
    if (user && user.needs_discogs_migration === true) {
      setShowMigration(true);
    }
  }, [user]);

  const isHome = location.pathname === '/' || location.pathname === '/hive';
  const hasInlineBack = location.pathname.startsWith('/record/') || location.pathname.startsWith('/vinyl/');
  
  return (
    <div className="min-h-screen relative" style={{ background: 'transparent', overflow: 'visible' }}>
      {/* BLOCK 585/587: Golden Glassy Banner — Discogs Import (relative: pushes navbar + content down) */}
      {showOAuthBanner && (
        <div className="relative w-full px-4 py-2.5 flex items-center justify-center gap-3 flex-wrap z-[200000]"
          style={{
            background: 'linear-gradient(135deg, rgba(255,223,107,0.95) 0%, rgba(244,181,33,0.93) 50%, rgba(218,165,32,0.91) 100%)',
            borderBottom: '1px solid rgba(184,134,11,0.3)',
            boxShadow: '0 2px 12px rgba(218,165,32,0.25)',
          }}
          data-testid="oauth-glassy-banner"
        >
          <Shield className="w-4 h-4 text-amber-900 shrink-0" />
          <span className="text-sm text-amber-900 font-medium">Want to import your collection? Connect your Discogs account to sync your library instantly.</span>
          <button
            onClick={handleOAuthClick}
            disabled={oauthLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition-all hover:scale-105 disabled:opacity-60"
            style={{ background: '#1A1A1A', color: '#FFD700', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}
            data-testid="oauth-banner-connect"
          >
            {oauthLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Shield className="w-3.5 h-3.5" />}
            Connect Discogs
          </button>
          <button
            onClick={handleSkipBanner}
            className="text-xs text-amber-900/60 hover:text-amber-900 transition-colors underline underline-offset-2"
            data-testid="oauth-banner-skip"
          >
            Skip for now
          </button>
          <button onClick={handleSkipBanner} className="text-amber-900/50 hover:text-amber-900 transition-colors ml-1" data-testid="oauth-banner-dismiss">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {user && <Navbar />}
      {user && !isHome && !hasInlineBack && (
        <button
          onClick={() => navigate(-1)}
          className="fixed z-40 flex items-center justify-center w-8 h-8 rounded-full text-stone-400/70 hover:text-stone-600 hover:bg-stone-200/40 transition-all left-3 md:left-5"
          style={{ top: '96px' }}
          data-testid="global-back-btn"
          aria-label="Go back"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
      )}
      <main className="relative z-10" style={{ overflow: 'visible' }}>
        {children}
      </main>
      <DiscogsSecurityModal open={showMigration} onClose={() => setShowMigration(false)} />
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
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-3 border-amber-300 border-t-amber-600 rounded-full animate-spin" /></div>}>
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

      {/* Public vinyl variant SEO pages — key forces full re-mount on URL change */}
      <Route path="/vinyl/:artist/:album/:variant" element={<AppLayout><VinylVariantPageWrapper /></AppLayout>} />
      <Route path="/variant/:releaseId" element={<AppLayout><VariantReleasePageWrapper /></AppLayout>} />

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
      <Route path="/honeypot/checkout/success" element={<ProtectedRoute><AppLayout><CheckoutSuccessPage /></AppLayout></ProtectedRoute>} />
      <Route path="/iso" element={<Navigate to="/honeypot" replace />} />
      <Route path="/trades" element={<ProtectedRoute><AppLayout><TradesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/messages" element={<ProtectedRoute><AppLayout><MessagesPage /></AppLayout></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/orders" element={<ProtectedRoute><AppLayout><OrdersPage /></AppLayout></ProtectedRoute>} />
      <Route path="/essentials" element={<ProtectedRoute><AppLayout><EssentialsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports" element={<ProtectedRoute><AppLayout><WaxReportPage /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports/history" element={<ProtectedRoute><AppLayout><WaxReportHistory /></AppLayout></ProtectedRoute>} />
      <Route path="/wax-reports/:reportId" element={<ProtectedRoute><AppLayout><WaxReportPage /></AppLayout></ProtectedRoute>} />
      <Route path="/reports/weekly" element={<ProtectedRoute><WeeklyReportPage /></ProtectedRoute>} />
      <Route path="/profile/:username" element={<ProtectedRoute><AppLayout><ProfilePage /></AppLayout></ProtectedRoute>} />
      <Route path="/record/:recordId" element={<ProtectedRoute><AppLayout><RecordDetailPage /></AppLayout></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin" element={<AdminRoute><AppLayout><AdminPage /></AppLayout></AdminRoute>} />
      <Route path="/admin/disputes" element={<AdminRoute><AppLayout><AdminDisputesPage /></AppLayout></AdminRoute>} />
      <Route path="/admin/beta" element={<Navigate to="/admin?section=beta" replace />} />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
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
          <SWRConfig value={{ revalidateOnFocus: false, dedupingInterval: 10000, errorRetryCount: 2 }}>
          <SocketProvider>
          <VariantModalProvider>
            <AppContent />
            <VariantModal />
            <Toaster />
          </VariantModalProvider>
          </SocketProvider>
          </SWRConfig>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
