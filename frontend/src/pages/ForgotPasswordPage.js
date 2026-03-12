import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ArrowLeft, Mail } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || window.location.origin;

const ForgotPasswordPage = () => {
  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password`, { email: identifier.trim() });
      setSent(true);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Something went wrong. Try again.';
      if (error.response?.status === 429) {
        toast.error('Too many requests. Please wait a few minutes.');
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4 py-12">
      <div className="honeycomb-bg absolute inset-0 opacity-50 pointer-events-none" />

      <Card className="w-full max-w-md relative z-10 border-honey/30 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex justify-center mb-4">
            <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-auto w-[200px]" />
          </Link>
          <CardTitle className="font-heading text-2xl">Reset Password</CardTitle>
          <CardDescription>
            {sent ? 'Check your inbox' : 'Enter your email or username'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="text-center space-y-4" data-testid="reset-sent-confirmation">
              <div className="w-14 h-14 mx-auto rounded-full bg-honey/20 flex items-center justify-center">
                <Mail className="w-7 h-7 text-honey-amber" />
              </div>
              <p className="text-sm text-muted-foreground">
                If an account exists for <strong>{identifier}</strong>, we've sent a password reset link. Check your email.
              </p>
              <Link to="/login">
                <Button variant="outline" className="mt-4 rounded-full" data-testid="back-to-login-btn">
                  <ArrowLeft className="w-4 h-4 mr-2" /> Back to Sign In
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="identifier">Email or Username</Label>
                <Input
                  id="identifier"
                  type="text"
                  placeholder="you@example.com or username"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  className="border-honey/50 focus:ring-honey"
                  data-testid="forgot-identifier-input"
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
                data-testid="forgot-submit-btn"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </Button>
              <div className="text-center">
                <Link to="/login" className="text-sm text-honey-amber hover:underline" data-testid="forgot-back-link">
                  Back to Sign In
                </Link>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ForgotPasswordPage;
