import React, { useState } from 'react';
import { Link, useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const { token: pathToken } = useParams();
  const token = pathToken || searchParams.get('token');
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/reset-password`, { token, password });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Reset failed. The link may have expired.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4">
        <Card className="w-full max-w-md border-honey/30 bg-white/80 backdrop-blur-sm">
          <CardContent className="pt-8 text-center space-y-4">
            <p className="text-muted-foreground">Invalid reset link.</p>
            <Link to="/forgot-password">
              <Button className="rounded-full bg-honey text-vinyl-black hover:bg-honey-amber">Request a New Link</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4 py-12">
      <div className="honeycomb-bg absolute inset-0 opacity-50 pointer-events-none" />

      <Card className="w-full max-w-md relative z-10 border-honey/30 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex justify-center mb-4">
            <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-auto w-[200px]" />
          </Link>
          <CardTitle className="font-heading text-2xl">
            {success ? 'Password Updated' : 'Set New Password'}
          </CardTitle>
          <CardDescription>
            {success ? 'Redirecting to sign in...' : 'Choose a new password for your account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {success ? (
            <div className="text-center space-y-4" data-testid="reset-success">
              <div className="w-14 h-14 mx-auto rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7 text-green-600" />
              </div>
              <p className="text-sm text-muted-foreground">Your password has been reset. Redirecting...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">New Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    className="border-honey/50 focus:ring-honey pr-10"
                    data-testid="reset-password-input"
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
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="border-honey/50 focus:ring-honey"
                  data-testid="reset-confirm-input"
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
                data-testid="reset-submit-btn"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ResetPasswordPage;
