import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import { usePageTitle } from '../hooks/usePageTitle';
import safeStorage from '../utils/safeStorage';

import { API_BASE } from '../utils/apiBase';
const API = API_BASE;

const JoinPage = () => {
  usePageTitle('Join the Hive');
  const [searchParams] = useSearchParams();
  const inviteCode = searchParams.get('code') || '';
  const emailParam = searchParams.get('email') || '';
  const navigate = useNavigate();
  const { setToken, setUser } = useAuth();

  const [form, setForm] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [codeInvalid, setCodeInvalid] = useState(!inviteCode);
  const [resendEmail, setResendEmail] = useState(emailParam);
  const [resendStatus, setResendStatus] = useState('');

  useEffect(() => {
    if (!inviteCode) {
      console.error('Invite Token Error: No invite code found in URL params');
      setCodeInvalid(true);
    }
  }, [inviteCode]);

  const handleResendInvite = async () => {
    if (!resendEmail || !resendEmail.includes('@')) {
      setResendStatus('Please enter a valid email address.');
      return;
    }
    setResendStatus('sending');
    try {
      const res = await fetch(`${API}/api/auth/resend-invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resendEmail }),
      });
      const data = await res.json();
      if (!res.ok) {
        console.error('Invite Token Error: Resend failed —', data.detail);
        setResendStatus(data.detail || 'Failed to send. Please try again.');
        return;
      }
      setResendStatus('sent');
    } catch (err) {
      console.error('Invite Token Error: Network error on resend —', err);
      setResendStatus('Network error. Please try again.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      toast.error('passwords do not match.');
      return;
    }
    if (form.password.length < 6) {
      toast.error('password must be at least 6 characters.');
      return;
    }
    if (form.username.length < 3) {
      toast.error('username must be at least 3 characters.');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/auth/register-invite`, {
        code: inviteCode,
        email: form.email,
        password: form.password,
        username: form.username,
      });
      const { access_token, user } = res.data;
      safeStorage.setItem('honeygroove_token', access_token);
      setToken(access_token);
      setUser(user);
      toast.success('welcome to the hive.');
      trackEvent('invite_used');
      navigate('/hive');
    } catch (err) {
      const detail = err.response?.data?.detail || 'Registration failed';
      console.error('Invite Token Error:', detail, '| Code:', inviteCode, '| Email:', form.email);
      if (detail.includes('invite code')) {
        setCodeInvalid(true);
      }
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  };

  const inputClass = 'w-full bg-[#FFFBF2] border border-[#D4A828]/20 rounded-xl px-4 py-3.5 font-serif text-base text-[#1E2A3A] placeholder:text-[#3A4D63]/50 focus:outline-none focus:border-[#D4A828] transition-colors';

  return (
    <div className="min-h-screen bg-[#FFFBF2] flex flex-col items-center" data-testid="join-page">
      <div className="w-full max-w-md mx-auto px-6" style={{ paddingTop: '80px' }}>
        {/* Logo */}
        <div className="flex justify-center mb-10">
          <Link to="/">
            <img src="/logo-drip.png" alt="the Honey Groove" className="h-20" data-testid="join-logo" />
          </Link>
        </div>

        {codeInvalid ? (
          <div className="text-center" data-testid="join-invalid-code">
            <h1
              className="mb-4"
              style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '36px', color: '#1E2A3A' }}
            >
              hmm, that didn't work.
            </h1>
            <p
              className="mb-6"
              style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: '22px', color: '#3A4D63', lineHeight: 1.5 }}
            >
              this invite code is invalid or has already been used.
            </p>

            {/* Resend invite fallback */}
            <div className="bg-white rounded-2xl p-6 mb-6 text-left" style={{ border: '1px solid rgba(200,134,26,0.15)' }}>
              <p className="text-center mb-4" style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '18px', color: '#915527', fontWeight: 600 }}>
                no worries — we'll send you a fresh link.
              </p>
              <input
                type="email"
                value={resendEmail}
                onChange={e => setResendEmail(e.target.value)}
                placeholder="enter your email"
                className="w-full bg-[#FFFBF2] border border-[#D4A828]/20 rounded-xl px-4 py-3.5 font-serif text-base text-[#1E2A3A] placeholder:text-[#3A4D63]/50 focus:outline-none focus:border-[#D4A828] transition-colors mb-3"
                data-testid="join-resend-email"
              />
              {resendStatus === 'sent' ? (
                <div className="bg-green-50 rounded-xl px-4 py-3 text-center" data-testid="join-resend-success">
                  <p className="text-sm text-green-700 font-medium">fresh invite sent! check your inbox.</p>
                </div>
              ) : (
                <button
                  onClick={handleResendInvite}
                  disabled={resendStatus === 'sending'}
                  className="w-full bg-[#915527] text-[#FDE68A] font-serif text-base font-medium rounded-2xl transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                  style={{ height: '52px' }}
                  data-testid="join-resend-btn"
                >
                  {resendStatus === 'sending' ? <Loader2 className="w-5 h-5 animate-spin" /> : 'send me a fresh invite link'}
                </button>
              )}
              {resendStatus && resendStatus !== 'sending' && resendStatus !== 'sent' && (
                <p className="text-sm text-red-500 text-center mt-2" data-testid="join-resend-error">{resendStatus}</p>
              )}
            </div>

            <p
              style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: '18px', color: '#3A4D63', lineHeight: 1.5 }}
            >
              or join the waitlist at{' '}
              <Link to="/beta" className="text-[#D4A828] underline">thehoneygroove.com/beta</Link>
            </p>
          </div>
        ) : (
          <>
            <h1
              className="text-center mb-2"
              style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '40px', color: '#1E2A3A' }}
            >
              you're invited.
            </h1>
            <p
              className="text-center mb-8"
              style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: '22px', color: '#D4A828' }}
            >
              create your account and join the hive.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4" data-testid="join-form">
              <input
                type="text"
                placeholder="username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })}
                className={inputClass}
                required
                minLength={3}
                maxLength={30}
                data-testid="join-username"
              />
              <input
                type="email"
                placeholder="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={inputClass}
                required
                data-testid="join-email"
              />
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className={`${inputClass} pr-12`}
                  required
                  minLength={6}
                  data-testid="join-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#3A4D63]/50 hover:text-[#3A4D63]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="confirm password"
                value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                className={inputClass}
                required
                data-testid="join-confirm-password"
              />

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#1E2A3A] font-serif text-lg font-medium rounded-2xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                style={{ height: '56px' }}
                data-testid="join-submit-btn"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'create my account'}
              </button>
            </form>

            <p className="text-center mt-6" style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '16px', color: '#3A4D63' }}>
              already have an account?{' '}
              <Link to="/login" className="text-[#D4A828] underline" data-testid="join-login-link">sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default JoinPage;
