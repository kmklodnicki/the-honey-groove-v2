import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Eye, EyeOff, Mail, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import safeStorage from '../utils/safeStorage';
import axios from 'axios';

import { API_BASE } from '../utils/apiBase';
const API = API_BASE;

/* Honeypot filling SVG animation */
const HoneypotLoader = () => (
  <div className="flex flex-col items-center gap-3 py-6" data-testid="honeypot-loader">
    <svg width="56" height="64" viewBox="0 0 56 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Drip from above */}
      <ellipse cx="28" cy="6" rx="3" ry="4" fill="#DAA520" opacity="0.8">
        <animate attributeName="cy" values="2;14;2" dur="1.4s" repeatCount="indefinite" />
        <animate attributeName="ry" values="4;2;4" dur="1.4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.9;0.4;0.9" dur="1.4s" repeatCount="indefinite" />
      </ellipse>
      {/* Pot body */}
      <path d="M10 24 C10 24 6 24 6 30 L8 52 C8 58 14 60 28 60 C42 60 48 58 48 52 L50 30 C50 24 46 24 46 24 Z" fill="#DAA520" opacity="0.15" stroke="#DAA520" strokeWidth="1.5" />
      {/* Honey fill rising */}
      <clipPath id="potClip">
        <path d="M10 24 C10 24 6 24 6 30 L8 52 C8 58 14 60 28 60 C42 60 48 58 48 52 L50 30 C50 24 46 24 46 24 Z" />
      </clipPath>
      <rect x="4" y="60" width="48" height="40" fill="#DAA520" opacity="0.5" clipPath="url(#potClip)">
        <animate attributeName="y" values="58;28;58" dur="2.8s" repeatCount="indefinite" />
      </rect>
      {/* Pot rim */}
      <rect x="8" y="20" rx="3" ry="3" width="40" height="6" fill="#DAA520" opacity="0.7" />
      {/* Handle */}
      <path d="M20 20 Q20 12 28 12 Q36 12 36 20" stroke="#DAA520" strokeWidth="2.5" fill="none" opacity="0.5" />
    </svg>
    <p className="text-sm font-medium animate-pulse" style={{ color: '#D4A828' }}>Warming up the honey...</p>
  </div>
);

const LoginPage = () => {
  usePageTitle('Sign In');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [unverified, setUnverified] = useState(false);
  const [resending, setResending] = useState(false);
  const { login, API: authAPI } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setUnverified(false);

    try {
      const userData = await login(email, password);

      // Pre-fetch feed + profile in background while navigating
      const token = safeStorage.getItem('honeygroove_token');
      if (token) {
        const headers = { Authorization: `Bearer ${token}` };
        axios.get(`${authAPI}/feed`, { params: { limit: 20 }, headers, timeout: 15000 }).catch(() => {});
        if (userData?.username) {
          axios.get(`${authAPI}/users/${userData.username}`, { headers, timeout: 15000 }).catch(() => {});
        }
      }

      toast.success('welcome back.');
      navigate('/hive');
    } catch (error) {
      const status = error.response?.status;
      if (status === 429) {
        toast.error('too many attempts. please try again in a few minutes.');
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        toast.error('The hive is a bit crowded right now! Please try one more time.');
      } else {
        const message = error.response?.data?.detail || 'The hive is a bit crowded right now! Please try one more time.';
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setResending(true);
    try {
      const token = safeStorage.getItem('honeygroove_token');
      await axios.post(`${API}/api/auth/resend-verification`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('verification email sent. check your inbox.');
    } catch {
      toast.error('could not send verification email. try again later.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4 py-12">
      <div className="honeycomb-bg absolute inset-0 opacity-50 pointer-events-none" />
      
      <Card className="w-full max-w-md relative z-10 border-honey/30 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex justify-center mb-4">
            <img 
              src="/logo-wordmark.png" 
              alt="the Honey Groove" 
              className="h-auto w-[200px]"
            />
          </Link>
          <CardTitle className="font-heading text-2xl">Welcome Back</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          {unverified && (
            <div className="mb-4 bg-[#F0E6C8] border border-[#E5DBC8] rounded-xl p-4" data-testid="email-verify-banner">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-[#D4A828] shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-[#1E2A3A] font-medium">Please verify your email address</p>
                  <p className="text-xs text-[#D4A828] mt-1">Check your inbox for a verification link.</p>
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    disabled={resending}
                    className="text-xs text-[#D4A828] hover:text-[#1E2A3A] underline mt-2 inline-flex items-center gap-1"
                    data-testid="resend-verification-btn"
                  >
                    {resending ? <><Loader2 className="w-3 h-3 animate-spin" /> Sending...</> : 'Resend verification email'}
                  </button>
                </div>
              </div>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            {loading ? (
              <HoneypotLoader />
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="email">Email or Username</Label>
                  <Input
                    id="email"
                    type="text"
                    placeholder="you@example.com or username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="border-honey/50 focus:ring-honey"
                    data-testid="login-email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="border-honey/50 focus:ring-honey pr-10"
                      data-testid="login-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
                  data-testid="login-submit"
                >
                  Sign In
                </Button>
              </>
            )}
          </form>

          <div className="mt-6 text-center text-sm space-y-2">
            <div>
              <Link to="/forgot-password" className="text-honey-amber hover:underline font-medium" data-testid="login-forgot-link">
                Forgot password?
              </Link>
            </div>
            <div>
              <span className="text-muted-foreground">Need an account? </span>
              <Link to="/beta" className="text-honey-amber hover:underline font-medium" data-testid="login-waitlist-link">
                Join the waitlist
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;
