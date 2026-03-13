import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ClaimInvitePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();
  const { setToken, setUser } = useAuth();

  const [email, setEmail] = useState('');
  const [isExisting, setIsExisting] = useState(false);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [status, setStatus] = useState('validating'); // validating | ready | submitting | success | error
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) { setStatus('error'); setError('No invite token found.'); return; }
    fetch(`${API}/api/auth/validate-invite?token=${encodeURIComponent(token)}`)
      .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
      .then(({ ok, data }) => {
        if (!ok) { setStatus('error'); setError(data.detail || 'Invalid invite link.'); return; }
        setEmail(data.email);
        setIsExisting(data.is_existing);
        setStatus('ready');
      })
      .catch(() => { setStatus('error'); setError('Could not validate invite. Please try again.'); });
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    setError('');
    setStatus('submitting');
    try {
      const res = await fetch(`${API}/api/auth/claim-invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Something went wrong.'); setStatus('ready'); return; }
      setStatus('success');
      // Auto-login
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        if (data.user) setUser(data.user);
        setTimeout(() => navigate(data.user?.onboarding_completed ? '/hive' : '/onboarding/building'), 1500);
      }
    } catch {
      setError('Network error. Please try again.');
      setStatus('ready');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#FAF6EE' }}>
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-10 mx-auto mb-2" />
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8" style={{ border: '1px solid rgba(145,85,39,0.1)' }}>

          {status === 'validating' && (
            <div className="text-center py-8" data-testid="claim-validating">
              <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto mb-3" style={{ borderColor: '#915527', borderTopColor: 'transparent' }} />
              <p className="text-sm" style={{ color: '#915527' }}>Validating your invite...</p>
            </div>
          )}

          {status === 'error' && !email && (
            <div className="text-center py-8" data-testid="claim-error">
              <p className="text-lg font-semibold mb-2" style={{ color: '#915527' }}>Invite Not Found</p>
              <p className="text-sm text-gray-500 mb-6">{error}</p>
              <a href="https://www.thehoneygroove.com" className="inline-block px-6 py-2 rounded-full text-sm font-semibold" style={{ background: '#FDE68A', color: '#915527' }}>
                Go to Home
              </a>
            </div>
          )}

          {(status === 'ready' || status === 'submitting' || (status === 'error' && email)) && (
            <>
              <h1 className="text-xl font-bold text-center mb-1" style={{ color: '#915527' }} data-testid="claim-title">
                {isExisting ? 'Welcome Back!' : 'Claim Your Invite'}
              </h1>
              <p className="text-sm text-center text-gray-500 mb-6">
                {isExisting ? 'Set a new password to get back into the hive.' : 'Set your password to join the hive.'}
              </p>

              <div className="bg-amber-50 rounded-lg px-4 py-2.5 mb-6 text-center" data-testid="claim-email">
                <span className="text-sm font-medium" style={{ color: '#915527' }}>{email}</span>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1.5 text-gray-700">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-amber-400 focus:ring-1 focus:ring-amber-400 outline-none transition-colors text-sm"
                    placeholder="At least 6 characters"
                    required
                    minLength={6}
                    autoFocus
                    data-testid="claim-password-input"
                  />
                </div>
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-1.5 text-gray-700">Confirm Password</label>
                  <input
                    type="password"
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-amber-400 focus:ring-1 focus:ring-amber-400 outline-none transition-colors text-sm"
                    placeholder="Type it again"
                    required
                    minLength={6}
                    data-testid="claim-confirm-input"
                  />
                </div>

                {error && (
                  <p className="text-sm text-red-500 text-center mb-4" data-testid="claim-error-msg">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={status === 'submitting'}
                  className="w-full py-3 rounded-full font-bold text-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                  style={{ background: '#915527', color: '#FDE68A' }}
                  data-testid="claim-submit-btn"
                >
                  {status === 'submitting' ? 'Setting up...' : isExisting ? 'Reset Password & Sign In' : 'Set Password & Join'}
                </button>
              </form>
            </>
          )}

          {status === 'success' && (
            <div className="text-center py-8" data-testid="claim-success">
              <div className="text-3xl mb-3">🎉</div>
              <p className="text-lg font-bold mb-1" style={{ color: '#915527' }}>You're in!</p>
              <p className="text-sm text-gray-500">Redirecting you to the hive...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
