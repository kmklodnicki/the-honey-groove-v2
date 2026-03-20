import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

import { API_BASE } from '../utils/apiBase';
const API = API_BASE;

const VerifyEmailPage = () => {
  usePageTitle('Verify Email');
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided.');
      return;
    }
    const verify = async () => {
      try {
        const res = await axios.get(`${API}/api/auth/verify-email?token=${token}`);
        setStatus('success');
        setMessage(res.data.message || 'Email verified successfully!');
        setTimeout(() => navigate('/login'), 3000);
      } catch (err) {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Verification failed. The link may have expired.');
      }
    };
    verify();
  }, [token, navigate]);

  return (
    <div className="min-h-screen bg-[#FFFBF2] flex items-center justify-center px-4" data-testid="verify-email-page">
      <div className="max-w-md w-full text-center">
        <Link to="/" className="inline-block mb-8">
          <img src="/logo-drip.png" alt="the Honey Groove" className="h-20 mx-auto" />
        </Link>

        {status === 'loading' && (
          <div className="space-y-4" data-testid="verify-loading">
            <Loader2 className="w-12 h-12 text-[#D4A828] animate-spin mx-auto" />
            <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '22px', color: '#3A4D63' }}>
              Verifying your email...
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4" data-testid="verify-success">
            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto" />
            <h1 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '36px', color: '#1E2A3A' }}>
              You're verified!
            </h1>
            <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '20px', color: '#3A4D63' }}>
              {message} Redirecting to sign in...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4" data-testid="verify-error">
            <XCircle className="w-16 h-16 text-red-400 mx-auto" />
            <h1 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '36px', color: '#1E2A3A' }}>
              Verification failed
            </h1>
            <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '20px', color: '#3A4D63' }}>
              {message}
            </p>
            <Link to="/login"
              className="inline-block mt-4 px-6 py-3 bg-[#E8A820] hover:bg-[#d49a1a] text-[#1E2A3A] rounded-full font-medium transition-colors"
              data-testid="verify-back-to-login">
              Back to Sign In
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;
