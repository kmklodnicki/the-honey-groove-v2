import React, { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { trackEvent } from '../utils/analytics';
import CrossfadeVideo from '../components/CrossfadeVideo';

import { API_BASE } from '../utils/apiBase';
const API = API_BASE;

const FEATURE_OPTIONS = [
  'Tracking my collection',
  'Sharing my spins and hauls',
  'Hunting my ISO',
  'Trading with other collectors',
  'The weekly Wax Report',
  'The daily prompt',
  'All of it honestly',
];

const BetaSignupPage = () => {
  const [form, setForm] = useState({ first_name: '', email: '', instagram_handle: '', feature_interest: '', website: '' });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [selectOpen, setSelectOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.first_name || !form.email || !form.instagram_handle || !form.feature_interest) {
      setError('all fields are required.');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/api/beta/signup`, form);
      trackEvent('beta_signup', { feature_interest: form.feature_interest });
      setSubmitted(true);
    } catch (err) {
      if (err.response?.status === 429) {
        setError('Too many attempts. Please try again in a few minutes.');
      } else {
        setError(err.response?.data?.detail || 'something went wrong. try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const inputClass = 'w-full bg-[#FFFBF2] border border-[#D4A828]/20 rounded-xl px-4 py-3.5 font-serif text-lg text-[#1E2A3A] placeholder:text-[#3A4D63]/50 focus:outline-none focus:border-[#D4A828] transition-colors';

  return (
    <>
      <Helmet>
        <title>Join the Beta · the Honey Groove&#8482;</title>
        <meta name="description" content="Get early access to the Honey Groove before public launch. Founding members get a permanent badge and a direct line to the founder." />
        <meta property="og:title" content="Join the Beta · the Honey Groove" />
        <meta property="og:description" content="Get early access to the Honey Groove before public launch. Founding members get a permanent badge and a direct line to the founder." />
        <meta property="og:image" content="/logo-drip.png" />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="min-h-screen bg-[#FFFBF2] flex flex-col items-center pb-16 relative" data-testid="beta-signup-page">
        {/* Honey drip · living video pinned flush to top */}
        <div
          className="absolute top-0 left-0 w-screen overflow-hidden z-0 flex"
          style={{ height: '120px', marginTop: '-1px', backgroundColor: '#FFFBF2' }}
          data-testid="beta-drip"
        >
          {[0,1,2].map(i => {
            const mask = i === 0
              ? 'linear-gradient(to right, black 92%, transparent 100%)'
              : i === 2
                ? 'linear-gradient(to left, black 92%, transparent 100%)'
                : 'linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%)';
            return (
            <CrossfadeVideo
              key={i}
              src="/honey-drip.mp4"
              poster="/honey-drip.png"
              className="block"
              mask={mask}
              style={{
                width: 'calc(100vw / 3 + 10px)',
                marginLeft: i === 0 ? 0 : '-5px',
                marginRight: i === 2 ? 0 : '-5px',
                objectFit: 'cover',
                objectPosition: 'top center',
                mixBlendMode: 'multiply',
              }}
            />
            );
          })}
        </div>

        <div className="w-full max-w-lg mx-auto px-6 relative z-10" style={{ paddingTop: '160px' }}>
          {/* Logo */}
          <div className="flex justify-center mb-4">
            <a href="/" data-testid="beta-logo-link">
              <img src="/logo-wordmark-clean.png" alt="the Honey Groove" className="w-[85vw] max-w-[520px]" data-testid="beta-logo" />
            </a>
          </div>

          {!submitted ? (
            <>
              {/* Headline */}
              <h1
                className="text-center mb-4"
                style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '64px', lineHeight: 1.1, color: '#1E2A3A' }}
                data-testid="beta-headline"
              >
                you found it.
              </h1>

              {/* Subhead */}
              <div className="text-center mb-6" style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: '28px', lineHeight: 1.4, color: '#D4A828' }}>
                <p>the Honey Groove<sup style={{ fontSize: '0.6em' }}>&trade;</sup> is almost ready.</p>
                <p>We're looking for Limited Founding Members to shape it.</p>
              </div>

              {/* Body copy */}
              <p
                className="text-center mb-8 mx-auto"
                style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: '20px', lineHeight: 1.6, color: '#3A4D63', maxWidth: '420px', padding: '0 12px' }}
              >
                Limited Founding Members get early access before public launch, a permanent founding member badge on their profile that never goes away, and a direct line to the founder during beta.
              </p>

              {/* Divider */}
              <div className="mx-auto mb-10" style={{ height: '1px', maxWidth: '320px', background: 'linear-gradient(90deg, transparent, #D4A82840, transparent)' }} />

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4" data-testid="beta-signup-form">
                <input
                  type="text"
                  placeholder="your first name"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className={inputClass}
                  required
                  data-testid="beta-first-name"
                />
                <input
                  type="email"
                  placeholder="your email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={inputClass}
                  required
                  data-testid="beta-email"
                />
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-serif text-lg text-[#3A4D63]/50">@</span>
                  <input
                    type="text"
                    placeholder="yourhandle"
                    value={form.instagram_handle}
                    onChange={(e) => setForm({ ...form, instagram_handle: e.target.value.replace(/^@/, '') })}
                    className={`${inputClass} pl-9`}
                    required
                    data-testid="beta-instagram"
                  />
                </div>

                {/* Custom select dropdown */}
                <div className="relative" data-testid="beta-feature-select">
                  <button
                    type="button"
                    onClick={() => setSelectOpen(!selectOpen)}
                    className={`${inputClass} text-left flex items-center justify-between`}
                    data-testid="beta-feature-trigger"
                  >
                    <span className={form.feature_interest ? 'text-[#1E2A3A]' : 'text-[#3A4D63]/50'}>
                      {form.feature_interest || 'what feature are you most excited about?'}
                    </span>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={`transition-transform ${selectOpen ? 'rotate-180' : ''}`}>
                      <path d="M4 6L8 10L12 6" stroke="#3A4D63" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                  </button>
                  {selectOpen && (
                    <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-[#FFFBF2] border border-[#D4A828]/20 rounded-xl shadow-lg overflow-hidden" data-testid="beta-feature-dropdown">
                      {FEATURE_OPTIONS.map((opt) => (
                        <button
                          key={opt}
                          type="button"
                          onClick={() => {
                            setForm({ ...form, feature_interest: opt });
                            setSelectOpen(false);
                          }}
                          className="w-full text-left px-4 py-3 font-serif text-base text-[#1E2A3A] hover:bg-[#D4A828]/10 transition-colors"
                          data-testid={`beta-feature-option-${opt.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {error && <p className="text-red-600 text-sm text-center font-serif" data-testid="beta-error">{error}</p>}

                {/* Honeypot field · invisible to humans, visible to bots */}
                <input
                  type="text"
                  name="website"
                  value={form.website}
                  onChange={e => setForm({ ...form, website: e.target.value })}
                  autoComplete="off"
                  tabIndex={-1}
                  style={{ position: 'absolute', left: '-9999px', opacity: 0, height: 0, width: 0, overflow: 'hidden' }}
                  aria-hidden="true"
                />

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#E8A820] hover:bg-[#d49a1a] text-[#1E2A3A] font-serif text-lg font-medium rounded-2xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  style={{ height: '56px' }}
                  data-testid="beta-submit-btn"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'add me to the list \uD83D\uDC1D'}
                </button>
              </form>
            </>
          ) : (
            /* Confirmation */
            <div className="text-center animate-fade-in" data-testid="beta-confirmation">
              <div style={{ fontSize: '80px', lineHeight: 1, marginBottom: '24px' }}>🍯</div>
              <h1
                style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: '56px', lineHeight: 1.1, color: '#1E2A3A', marginBottom: '20px' }}
              >
                you're on the list.
              </h1>
              <p
                style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: '24px', lineHeight: 1.5, color: '#3A4D63', maxWidth: '380px', margin: '0 auto' }}
              >
                i'll be in touch soon with everything you need to know to get started testing. follow{' '}
                <a href="https://www.instagram.com/thehoneygroove" target="_blank" rel="noopener noreferrer" style={{ color: '#D4A828', textDecoration: 'underline' }}>@thehoneygroove</a>
                {' '}for updates.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default BetaSignupPage;
