import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import Navbar from "./components/Navbar";

// Pages
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import HivePage from "./pages/HivePage";
import ExplorePage from "./pages/ExplorePage";
import CollectionPage from "./pages/CollectionPage";
import AddRecordPage from "./pages/AddRecordPage";
import ProfilePage from "./pages/ProfilePage";
import RecordDetailPage from "./pages/RecordDetailPage";
import SettingsPage from "./pages/SettingsPage";
import CreateHaulPage from "./pages/CreateHaulPage";
import ISOPage from "./pages/ISOPage";

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-honey-cream flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 bg-honey rounded-full animate-pulse mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

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
      {/* Public routes */}
      <Route path="/" element={<LandingWrapper />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/explore" element={
        <AppLayout>
          <ExplorePage />
        </AppLayout>
      } />

      {/* Protected routes */}
      <Route path="/hive" element={
        <ProtectedRoute>
          <AppLayout>
            <HivePage />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/collection" element={
        <ProtectedRoute>
          <AppLayout>
            <CollectionPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/add-record" element={
        <ProtectedRoute>
          <AppLayout>
            <AddRecordPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/create-haul" element={
        <ProtectedRoute>
          <AppLayout>
            <CreateHaulPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/iso" element={
        <ProtectedRoute>
          <AppLayout>
            <ISOPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout>
            <SettingsPage />
          </AppLayout>
        </ProtectedRoute>
      } />

      {/* Semi-public routes (viewable by all, some features require auth) */}
      <Route path="/profile/:username" element={
        <AppLayout>
          <ProfilePage />
        </AppLayout>
      } />
      <Route path="/record/:recordId" element={
        <AppLayout>
          <RecordDetailPage />
        </AppLayout>
      } />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
        <Toaster position="top-center" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
