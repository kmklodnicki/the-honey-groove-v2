import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Disc, Eye, EyeOff, Mail, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';
import safeStorage from '../utils/safeStorage';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const LoginPage = () => {
  usePageTitle('Sign In');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [unverified, setUnverified] = useState(false);
  const [resending, setResending] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setUnverified(false);

    try {
      const userData = await login(email, password);
      toast.success('welcome back.');
      navigate('/hive');
    } catch (error) {
      const status = error.response?.status;
      if (status === 429) {
        toast.error('too many attempts. please try again in a few minutes.');
      } else {
        const message = error.response?.data?.detail || 'Invalid email or password';
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
            <div className="mb-4 bg-amber-50 border border-amber-200 rounded-xl p-4" data-testid="email-verify-banner">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-amber-800 font-medium">Please verify your email address</p>
                  <p className="text-xs text-amber-700 mt-1">Check your inbox for a verification link.</p>
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    disabled={resending}
                    className="text-xs text-amber-600 hover:text-amber-800 underline mt-2 inline-flex items-center gap-1"
                    data-testid="resend-verification-btn"
                  >
                    {resending ? <><Loader2 className="w-3 h-3 animate-spin" /> Sending...</> : 'Resend verification email'}
                  </button>
                </div>
              </div>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
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
              disabled={loading}
              className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
              data-testid="login-submit"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
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
