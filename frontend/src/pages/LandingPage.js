import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ArrowLeftRight, X, Loader2, Shield, CheckCircle2, ArrowRight } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import SEOHead from '../components/SEOHead';

// Design tokens
const GOLD = '#D4A828';
const GOLD_LIGHT = '#E8CA5A';
const NAVY = '#1E2A3A';
const SLATE = '#3A4D63';
const CREAM = '#F0E6C8';
const CREAM_DARK = '#F3EBE0';

const HONEYCOMB_SVG = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='100'%3E%3Cpath d='M28 66L0 50V18L28 2l28 16v32L28 66zm0 0v34M0 50L28 66M56 50L28 66' fill='none' stroke='%23D4A828' stroke-width='1'/%3E%3C/svg%3E")`;

// Smooth crossfade looping video background
const SmoothLoopVideo = ({ src, opacity, style }) => {
  const aRef = useRef(null);
  const bRef = useRef(null);
  const stateRef = useRef({ active: null, waiting: null, fading: false });

  useEffect(() => {
    const a = aRef.current;
    const b = bRef.current;
    if (!a || !b) return;
    stateRef.current = { active: a, waiting: b, fading: false };
    const FADE_S = 1.8;

    const tick = (startMs, fromOpacity, toOpacity, onDone) => {
      const step = (now) => {
        const t = Math.min((now - startMs) / (FADE_S * 1000), 1);
        const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
        const { active, waiting } = stateRef.current;
        active.style.opacity = String(fromOpacity * (1 - ease));
        waiting.style.opacity = String(toOpacity * ease);
        if (t < 1) requestAnimationFrame(step);
        else onDone();
      };
      requestAnimationFrame(step);
    };

    const onTimeUpdate = () => {
      const { active, waiting, fading } = stateRef.current;
      if (fading || !active.duration) return;
      const remaining = active.duration - active.currentTime;
      if (remaining > FADE_S) return;

      stateRef.current.fading = true;
      waiting.currentTime = 0;
      waiting.play().catch(() => {});

      tick(performance.now(), opacity, opacity, () => {
        active.pause();
        active.style.opacity = '0';
        waiting.style.opacity = String(opacity);
        stateRef.current = { active: waiting, waiting: active, fading: false };
      });
    };

    a.addEventListener('timeupdate', onTimeUpdate);
    b.addEventListener('timeupdate', onTimeUpdate);
    return () => {
      a.removeEventListener('timeupdate', onTimeUpdate);
      b.removeEventListener('timeupdate', onTimeUpdate);
    };
  }, [opacity]);

  const base = { ...style, position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' };
  return (
    <>
      <video ref={aRef} autoPlay muted playsInline src={src} style={{ ...base, opacity }} data-testid="hero-drip-video" />
      <video ref={bRef} muted playsInline src={src} style={{ ...base, opacity: 0 }} />
    </>
  );
};

const HoneycombBg = ({ children, style = {} }) => (
  <div style={{ position: 'relative', ...style }}>
    <div style={{
      position: 'absolute', inset: 0,
      backgroundImage: HONEYCOMB_SVG,
      backgroundSize: '56px 100px',
      opacity: 0.06,
      pointerEvents: 'none',
    }} />
    {children}
  </div>
);

const Nav = ({ onJoin }) => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  // Lock body scroll when menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

  const navLinks = [
    { label: 'Features', href: '#features' },
    { label: 'Marketplace', href: '#marketplace' },
    { label: 'Community', href: '#community' },
  ];

  return (
    <>
      <nav
        style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
          background: scrolled || menuOpen ? NAVY : 'transparent',
          boxShadow: scrolled && !menuOpen ? '0 2px 16px rgba(0,0,0,0.25)' : 'none',
          transition: 'background 0.3s, box-shadow 0.3s',
          padding: '0 20px',
        }}
        data-testid="navbar"
      >
        <div style={{ maxWidth: 1152, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          {/* Text logo */}
          <span style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, letterSpacing: '-0.01em', flexShrink: 0 }}>
            <em style={{ color: GOLD }}>the</em>
            <span style={{ color: '#fff', marginLeft: 6 }}>Honey</span>
            <span style={{ color: GOLD, marginLeft: 4 }}>Groove</span>
          </span>

          {/* Desktop nav links — hidden on mobile */}
          <div className="hidden md:flex" style={{ alignItems: 'center', gap: 28 }}>
            {navLinks.map(l => (
              <a key={l.label} href={l.href} style={{ color: 'rgba(255,255,255,0.75)', textDecoration: 'none', fontSize: 14, fontWeight: 500 }}
                className="hover:text-white transition-colors">{l.label}</a>
            ))}
            <button
              onClick={onJoin}
              style={{ background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`, color: NAVY, border: 'none', borderRadius: 9999, padding: '8px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
              data-testid="nav-join-btn"
            >
              Join the Hive
            </button>
          </div>

          {/* Mobile right side: CTA + hamburger */}
          <div className="flex md:hidden" style={{ alignItems: 'center', gap: 10 }}>
            <button
              onClick={onJoin}
              style={{ background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`, color: NAVY, border: 'none', borderRadius: 9999, padding: '7px 14px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
              data-testid="nav-join-btn"
            >
              Join
            </button>
            <button
              onClick={() => setMenuOpen(o => !o)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 6, color: '#fff' }}
              aria-label="Toggle menu"
            >
              {menuOpen ? (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              ) : (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="8" x2="21" y2="8"/><line x1="3" y1="16" x2="21" y2="16"/></svg>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile full-screen overlay menu */}
      {menuOpen && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 99, background: NAVY, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 40 }}
          className="md:hidden"
        >
          {navLinks.map(l => (
            <a
              key={l.label}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              style={{ color: '#fff', textDecoration: 'none', fontFamily: "'Playfair Display', serif", fontSize: 32, fontWeight: 700 }}
            >
              {l.label}
            </a>
          ))}
          <button
            onClick={() => { setMenuOpen(false); onJoin(); }}
            style={{ background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`, color: NAVY, border: 'none', borderRadius: 9999, padding: '14px 40px', fontSize: 18, fontWeight: 700, cursor: 'pointer', marginTop: 8 }}
          >
            Join the Hive
          </button>
        </div>
      )}
    </>
  );
};

const FALLBACK_TESTIMONIALS = [
  { id: 'f1', username: '@crazy_vinyl_13', quote: "I have been waiting for something like this. Discogs is for cataloging, eBay is for selling, but nothing was for the community. The Honey Groove is where I actually want to hang out.", label: 'beta collector', avatarLetter: 'C', recordCount: 187 },
  { id: 'f2', username: '@crateking', quote: "The Wax Report personality cards are addicting. I share mine every Monday morning and my followers keep asking how to join.", label: 'founding collector', avatarLetter: 'C', recordCount: 312 },
  { id: 'f3', username: '@waxvault99', quote: "6% fees? I was paying almost 13% on other platforms. I moved all my listings here the first week. The Mutual Hold system makes trading feel safe for the first time ever.", label: 'beta collector', avatarLetter: 'W', recordCount: 94 },
];

const LandingPage = () => {
  usePageTitle();
  const navigate = useNavigate();
  const { user, API } = useAuth();
  const [popupOpen, setPopupOpen] = useState(false);
  const [waitlistOpen, setWaitlistOpen] = useState(false);
  const [nlEmail, setNlEmail] = useState('');
  const [nlLoading, setNlLoading] = useState(false);
  const [nlSuccess, setNlSuccess] = useState(false);
  const [popupEmail, setPopupEmail] = useState('');
  const [popupLoading, setPopupLoading] = useState(false);
  const [popupSuccess, setPopupSuccess] = useState(false);

  // Testimonials (fetched from API)
  const [testimonials, setTestimonials] = useState(FALLBACK_TESTIMONIALS);
  useEffect(() => {
    fetch(`${API}/testimonials`)
      .then(r => r.json())
      .then(data => { if (Array.isArray(data) && data.length > 0) setTestimonials(data); })
      .catch(() => {}); // keep fallback on error
  }, [API]);

  // Carousel state
  const [current, setCurrent] = useState(0);
  const [fade, setFade] = useState(true);
  const carouselTimer = useRef(null);

  const goTo = (idx) => {
    setFade(false);
    setTimeout(() => {
      setCurrent((idx + testimonials.length) % testimonials.length);
      setFade(true);
    }, 200);
  };

  useEffect(() => {
    carouselTimer.current = setInterval(() => {
      goTo(current + 1);
    }, 6000);
    return () => clearInterval(carouselTimer.current);
  }, [current, goTo]); // eslint-disable-line react-hooks/exhaustive-deps

  // 30s delayed popup for non-logged-in visitors (once per session)
  useEffect(() => {
    if (user) return;
    const dismissed = sessionStorage.getItem('nl_popup_dismissed');
    if (dismissed) return;
    const timer = setTimeout(() => setPopupOpen(true), 30000);
    return () => clearTimeout(timer);
  }, [user]);

  const dismissPopup = () => {
    setPopupOpen(false);
    sessionStorage.setItem('nl_popup_dismissed', '1');
  };

  const handleSubscribe = async (email, setLoading, setSuccess) => {
    if (!email || !email.includes('@')) { toast.error('Enter a valid email'); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/newsletter/subscribe`, { email, source: 'landing_page' });
      setSuccess(true);
      toast.success('subscribed!');
    } catch { toast.error('something went wrong'); }
    finally { setLoading(false); }
  };

  const features = [
    { icon: '📀', title: 'Track Your Vault', description: "Know exactly what you own and what it's worth. Every record in your vault shows its current market value, updated regularly." },
    { icon: '🎵', title: 'Now Spinning', description: 'Drop the needle, share the moment. Log your spin, pick a mood, and let the hive know what\'s on the turntable right now.' },
    { icon: '🍯', title: 'The Honeypot', description: 'A peer-to-peer marketplace where collectors buy, sell, and trade directly. Lower fees than any major vinyl marketplace — because you should keep more of what your records are worth.' },
    { icon: '🔍', title: 'ISO', description: "Post what you've been hunting. Get matched with collectors who have it. We notify you the moment your record appears — so you never miss it again." },
    { icon: '🤝', title: 'Trade with Confidence', description: 'Every trade protected by a Mutual Hold. Both parties put up a hold equal to the estimated record value. Fully reversed on delivery. No risk, no blind trust.' },
    { icon: '📊', title: 'Your Week in Wax', description: 'Every Sunday a full breakdown of your listening week — top artists, moods, eras, and a one-line summary of who you were as a listener. Shareable to Instagram Stories in one tap.' },
  ];

  return (
    <div className="min-h-screen" style={{ background: CREAM_DARK }}>
      <SEOHead
        title="The Vinyl Social Club, Finally."
        description="Track your vinyl collection, discover rare pressings, buy, sell, and trade records with collectors worldwide. Join The Honey Groove."
        url="/"
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'WebApplication',
          name: 'The Honey Groove',
          url: 'https://thehoneygroove.com',
          description: 'Social vinyl tracking platform for record collectors. Track your vinyl collection, log spins, discover new music, and connect with collectors worldwide.',
          applicationCategory: 'SocialNetworkingApplication',
          operatingSystem: 'Web',
          offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
          keywords: 'vinyl, record collection, vinyl tracking, record collectors, vinyl social network, now spinning, vinyl marketplace, rare pressings, colored vinyl',
        }}
      />

      <Nav onJoin={() => setWaitlistOpen(true)} />

      {/* ── HERO ── */}
      <section
        style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden', background: NAVY, display: 'flex', alignItems: 'center' }}
        data-testid="hero-drip"
      >
        {/* Smooth crossfade looping video background */}
        <SmoothLoopVideo src="https://res.cloudinary.com/daobevscb/video/upload/v1774042930/new-honey-drip_q6wemf.mp4" opacity={0.35} style={{ zIndex: 0 }} />
        {/* Bottom fade to cream */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: 160,
          background: `linear-gradient(to bottom, transparent, ${CREAM_DARK})`,
          zIndex: 1,
        }} />

        {/* Hero content */}
        <div style={{ position: 'relative', zIndex: 2, width: '100%', maxWidth: 900, margin: '0 auto', padding: '120px 24px 80px', textAlign: 'center' }}>
          {/* Beta badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(212,168,40,0.15)', border: `1px solid ${GOLD}40`,
            borderRadius: 9999, padding: '6px 18px', marginBottom: 32,
          }}>
            <span style={{ color: GOLD, fontSize: 13, fontWeight: 600, letterSpacing: '0.04em' }}>
              Now in beta with 100+ collectors
            </span>
          </div>

          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 'clamp(40px, 7vw, 80px)',
            fontWeight: 700,
            color: '#fff',
            lineHeight: 1.1,
            marginBottom: 24,
          }}>
            the vinyl social club,{' '}
            <span style={{ background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontStyle: 'italic' }}>
              finally.
            </span>
          </h1>

          <p style={{ color: '#F0E6C8', fontSize: 'clamp(16px, 2.5vw, 20px)', marginBottom: 40, maxWidth: 600, margin: '0 auto 40px', lineHeight: 1.6 }}>
            track your records, share your hauls, hunt down your ISO, and trade with people who get it.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <button
              onClick={() => setWaitlistOpen(true)}
              style={{
                background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                color: NAVY, border: 'none', borderRadius: 9999,
                padding: '16px 40px', fontSize: 18, fontWeight: 700,
                cursor: 'pointer', letterSpacing: '0.01em',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              data-testid="hero-signup-btn"
            >
              Join the Hive
            </button>
            <Link
              to="/login"
              style={{ color: 'rgba(240,230,200,0.7)', fontSize: 14, textDecoration: 'none' }}
              className="hover:text-white transition-colors"
              data-testid="hero-login-link"
            >
              already a collector? sign in →
            </Link>
          </div>
        </div>
      </section>

      {/* ── STATS BAR ── */}
      <section style={{ background: NAVY, padding: '40px 0' }} data-testid="stats-strip">
        <div style={{ maxWidth: 1024, margin: '0 auto', padding: '0 24px' }}>
          <div className="grid grid-cols-2 lg:grid-cols-4" style={{ gap: 0 }}>
            {[
              { num: '6%', label: 'transaction fee. lower than everywhere else.' },
              { num: 'Free', label: 'to join. always.' },
              { num: '100%', label: 'of trade holds reversed on confirmed delivery.' },
              { num: 'Limited', label: 'Founding Members. Join the hive.' },
            ].map((stat, i) => (
              <div
                key={i}
                className={[
                  // right border on col 0 always, col 1 on desktop only, col 2 on desktop only
                  i === 0 ? 'border-r' : '',
                  i === 1 ? 'lg:border-r' : '',
                  i === 2 ? 'lg:border-r' : '',
                  // bottom border on top row (items 0+1) on mobile only
                  i < 2 ? 'border-b lg:border-b-0' : '',
                ].join(' ')}
                style={{
                  textAlign: 'center',
                  borderColor: SLATE,
                  padding: '24px 12px',
                }}
                data-testid={`stat-${i}`}
              >
                <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(32px, 8vw, 52px)', fontWeight: 700, color: GOLD, fontStyle: 'italic', lineHeight: 1 }}>
                  {stat.num}
                </div>
                <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 'clamp(12px, 3vw, 15px)', color: CREAM, marginTop: 8, lineHeight: 1.4 }}>
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <HoneycombBg id="features" style={{ background: '#FAF7F2' }}>
        <section id="features" className="py-10 md:py-20" style={{ position: 'relative' }}>
          <div style={{ maxWidth: 1152, margin: '0 auto', padding: '0 24px' }}>
            <div style={{ textAlign: 'center', marginBottom: 56 }}>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(28px, 4vw, 44px)', color: '#1F1F1F', marginBottom: 12 }}>
                built for the <em style={{ color: GOLD }}>obsessed.</em>
              </h2>
              <p style={{ color: '#1F1F1F99', fontSize: 17, maxWidth: 520, margin: '0 auto' }}>
                The Honey Groove is designed by collectors, for collectors. Here's what makes our hive different.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((f) => (
                <div
                  key={f.title}
                  style={{
                    background: 'rgba(255,255,255,0.7)',
                    backdropFilter: 'blur(4px)',
                    border: `1px solid #E5DBC8`,
                    borderRadius: 16,
                    padding: 24,
                  }}
                  data-testid={`feature-${f.title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <div style={{ fontSize: 28, marginBottom: 12 }}>{f.icon}</div>
                  <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 20, color: '#1F1F1F', marginBottom: 8 }}>{f.title}</h3>
                  <p style={{ color: '#1F1F1F99', fontSize: 14, lineHeight: 1.6 }}>{f.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </HoneycombBg>

      {/* ── TRADE / MUTUAL HOLD ── */}
      <section id="marketplace" style={{ padding: '80px 0', background: CREAM_DARK }} data-testid="mutual-hold-spotlight">
        <div style={{ maxWidth: 1152, margin: '0 auto', padding: '0 24px' }}>
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left */}
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: GOLD, marginBottom: 16 }}>
                TRADE WITH CONFIDENCE
              </p>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(28px, 4vw, 52px)', lineHeight: 1.1, fontWeight: 700, color: '#1F1F1F', marginBottom: 20 }}>
                Both parties protected.{' '}
                <em style={{ color: GOLD }}>Every single trade.</em>
              </h2>
              <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 19, color: SLATE, lineHeight: 1.7, marginBottom: 24 }}>
                Every trade on the Honey Groove requires a Mutual Hold. Both collectors put up a hold equal to the estimated value of the records being traded. The hold is fully reversed within 48 hours of confirmed delivery on both sides. Nobody walks away ahead by scamming. The math makes it impossible.
              </p>
              <Link to="/faq#trades" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, color: GOLD, textDecoration: 'none' }} data-testid="learn-hold-link">
                Learn how it works <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Right — diagram */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div
                style={{ width: '100%', maxWidth: 400, borderRadius: 24, border: `2px solid ${GOLD}25`, background: 'rgba(255,255,255,0.6)', padding: 40 }}
                data-testid="hold-diagram"
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
                  {/* Collector A */}
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      width: 64, height: 64, borderRadius: '50%',
                      background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      margin: '0 auto 8px', fontSize: 28,
                    }}>🎵</div>
                    <p style={{ fontSize: 12, color: '#1F1F1F99', fontWeight: 500 }}>Collector A</p>
                  </div>

                  {/* Arrow */}
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: `${GOLD}80`, fontSize: 22 }}>
                    <div style={{ height: 1, flex: 1, background: `${GOLD}30` }} />
                    <span style={{ margin: '0 8px' }}>⇄</span>
                    <div style={{ height: 1, flex: 1, background: `${GOLD}30` }} />
                  </div>

                  {/* Collector B */}
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      width: 64, height: 64, borderRadius: '50%',
                      background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      margin: '0 auto 8px', fontSize: 28,
                    }}>📀</div>
                    <p style={{ fontSize: 12, color: '#1F1F1F99', fontWeight: 500 }}>Collector B</p>
                  </div>
                </div>

                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                    background: `${GOLD}18`, border: `1px solid ${GOLD}30`,
                    borderRadius: 9999, padding: '10px 20px',
                  }}>
                    <Shield className="w-5 h-5" style={{ color: GOLD }} />
                    <span style={{ fontSize: 14, fontWeight: 700, color: GOLD }}>Hold Active</span>
                  </div>
                </div>

                <div style={{ borderTop: `1px dashed ${GOLD}30`, paddingTop: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <CheckCircle2 className="w-5 h-5" style={{ color: GOLD }} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: GOLD }}>Delivery Confirmed · Holds Released</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEE COMPARISON ── */}
      <section style={{ padding: '64px 0', background: CREAM }} data-testid="fee-comparison">
        <div style={{ maxWidth: 540, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(26px, 3.5vw, 38px)', color: '#1F1F1F', marginBottom: 12 }}>
            Finally. A marketplace that's <em style={{ color: GOLD }}>on your side.</em>
          </h2>
          <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 18, color: SLATE, marginBottom: 36, fontStyle: 'italic' }}>
            we charge less so you keep more.
          </p>
          <div style={{ borderRadius: 16, overflow: 'hidden', border: `1px solid ${GOLD}25`, background: 'rgba(255,255,255,0.85)' }} data-testid="fee-table">
            {[
              { name: 'Other Platforms', fee: '12.9%', highlight: false, gold: false },
              { name: 'Competitors', fee: '8%', highlight: false, gold: false },
              { name: 'The Honey Groove™', fee: '6%', highlight: true, gold: false },
              { name: 'Gold Collectors', fee: '4%', highlight: false, gold: true },
            ].map((row) => (
              <div
                key={row.name}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '16px 24px',
                  background: row.gold
                    ? `linear-gradient(135deg, ${GOLD}22, ${GOLD_LIGHT}18)`
                    : row.highlight
                      ? `${GOLD}18`
                      : 'transparent',
                  borderLeft: row.highlight ? `3px solid ${GOLD}` : row.gold ? `3px solid ${GOLD_LIGHT}` : 'none',
                  borderBottom: !row.gold ? `1px solid ${GOLD}15` : 'none',
                  fontWeight: row.highlight || row.gold ? 700 : 400,
                  color: row.highlight || row.gold ? '#1F1F1F' : '#1F1F1F80',
                }}
                data-testid={`fee-row-${row.name.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: row.highlight || row.gold ? 15 : 13 }}>{row.name}</span>
                  {row.gold && (
                    <span style={{
                      fontSize: 10, fontWeight: 800, letterSpacing: '0.08em',
                      background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                      color: NAVY, borderRadius: 4, padding: '2px 7px',
                    }}>GOLD</span>
                  )}
                </div>
                <span style={{ fontSize: row.highlight || row.gold ? 20 : 13, color: row.highlight || row.gold ? GOLD : '#1F1F1F80' }}>
                  {row.fee}
                </span>
              </div>
            ))}
          </div>
          <p style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 14, color: SLATE, marginTop: 20, fontStyle: 'italic' }}>
            fees apply to completed sales only. trades with no sweetener are always free.
          </p>
        </div>
      </section>

      {/* ── SOCIAL PROOF CAROUSEL ── */}
      <section id="community" style={{ background: NAVY, padding: '80px 0', position: 'relative', overflow: 'hidden' }} data-testid="testimonials-section">
        {/* Honeycomb overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: HONEYCOMB_SVG,
          backgroundSize: '56px 100px',
          opacity: 0.04,
          pointerEvents: 'none',
        }} />

        <div style={{ maxWidth: 720, margin: '0 auto', padding: '0 24px', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', color: GOLD, marginBottom: 12 }}>
            FROM THE HIVE
          </p>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(26px, 3.5vw, 38px)', color: '#fff', marginBottom: 48 }}>
            Collectors who get it.
          </h2>

          {/* Testimonial card */}
          <div style={{
            opacity: fade ? 1 : 0,
            transform: fade ? 'translateY(0)' : 'translateY(8px)',
            transition: 'opacity 0.3s ease, transform 0.3s ease',
            background: 'rgba(255,255,255,0.06)', border: `1px solid rgba(255,255,255,0.1)`,
            borderRadius: 20, padding: '40px 48px', marginBottom: 36,
          }}>
            {/* Decorative quote mark */}
            <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 60, color: `${GOLD}33`, lineHeight: 1, marginBottom: 8, textAlign: 'left' }}>"</div>
            <p style={{ color: '#fff', fontSize: 'clamp(16px, 2vw, 20px)', lineHeight: 1.7, fontFamily: "'Playfair Display', serif", marginBottom: 28, fontStyle: 'italic', textAlign: 'left' }}>
              {testimonials[current]?.quote || ''}
            </p>
            {/* User card */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {testimonials[current]?.avatarUrl ? (
                <img src={testimonials[current].avatarUrl} alt="" style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover' }} />
              ) : (
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: 15, color: NAVY,
                }}>
                  {testimonials[current]?.avatarLetter || '?'}
                </div>
              )}
              <div style={{ textAlign: 'left' }}>
                <p style={{ color: '#fff', fontSize: 12, fontWeight: 700, margin: 0 }}>{testimonials[current]?.username || ''}</p>
                <p style={{ color: CREAM, fontSize: 10, margin: 0, opacity: 0.75 }}>
                  {testimonials[current]?.label || ''}{testimonials[current]?.recordCount ? ` · ${testimonials[current].recordCount} records` : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Arrows */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginBottom: 24 }}>
            <button
              onClick={() => { clearInterval(carouselTimer.current); goTo(current - 1); }}
              style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 40, height: 40, color: '#fff', fontSize: 18, cursor: 'pointer' }}
              aria-label="Previous testimonial"
            >←</button>
            <button
              onClick={() => { clearInterval(carouselTimer.current); goTo(current + 1); }}
              style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 40, height: 40, color: '#fff', fontSize: 18, cursor: 'pointer' }}
              aria-label="Next testimonial"
            >→</button>
          </div>

          {/* Dot indicators */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            {testimonials.map((_, i) => (
              <button
                key={i}
                onClick={() => { clearInterval(carouselTimer.current); goTo(i); }}
                style={{
                  border: 'none', borderRadius: 9999, cursor: 'pointer',
                  width: i === current ? 24 : 8,
                  height: 8,
                  background: i === current ? GOLD : 'rgba(255,255,255,0.25)',
                  transition: 'width 0.3s, background 0.3s',
                  padding: 0,
                }}
                aria-label={`Go to testimonial ${i + 1}`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── NEWSLETTER ── */}
      <HoneycombBg>
        <section style={{ padding: '64px 0', background: '#FAF7F2', position: 'relative' }} data-testid="newsletter-section">
          <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(26px, 3.5vw, 38px)', color: '#1F1F1F', marginBottom: 12 }}>
              stay in the loop
            </h2>
            <p style={{ color: '#1F1F1F80', fontSize: 15, marginBottom: 32, lineHeight: 1.7 }}>
              a weekly letter for collectors. new finds, community stories, and what's buzzing in the hive. no spam, just wax.
            </p>
            {nlSuccess ? (
              <p style={{ color: GOLD, fontWeight: 600, fontSize: 18 }}>you're in! welcome to the hive 🍯</p>
            ) : (
              <div style={{ display: 'flex', gap: 8, maxWidth: 440, margin: '0 auto' }}>
                <Input
                  type="email"
                  placeholder="your email address"
                  value={nlEmail}
                  onChange={e => setNlEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubscribe(nlEmail, setNlLoading, setNlSuccess)}
                  style={{ flex: 1, border: `1px solid #E5DBC8`, background: '#fff' }}
                  data-testid="newsletter-email-input"
                />
                <button
                  onClick={() => handleSubscribe(nlEmail, setNlLoading, setNlSuccess)}
                  disabled={nlLoading}
                  style={{
                    background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                    color: NAVY, border: 'none', borderRadius: 9999,
                    padding: '0 24px', fontSize: 14, fontWeight: 700,
                    cursor: nlLoading ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap',
                    display: 'flex', alignItems: 'center', gap: 6,
                  }}
                  data-testid="newsletter-subscribe-btn"
                >
                  {nlLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'subscribe 🍯'}
                </button>
              </div>
            )}
          </div>
        </section>
      </HoneycombBg>

      {/* ── FINAL CTA ── */}
      <section style={{ padding: '80px 0', background: CREAM_DARK }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <div style={{
            background: 'linear-gradient(135deg, #F0E6C8, #F3EBE0)',
            borderRadius: 24, padding: '64px 48px',
            border: `1px solid ${GOLD}30`,
          }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 'clamp(28px, 4vw, 44px)', color: '#1F1F1F', marginBottom: 16 }}>
              Ready to Join The Hive?
            </h2>
            <p style={{ color: '#1F1F1F99', fontSize: 17, marginBottom: 32, maxWidth: 480, margin: '0 auto 32px' }}>
              you've been waiting for this. so have we.
            </p>
            <button
              onClick={() => setWaitlistOpen(true)}
              style={{
                background: NAVY, color: CREAM, border: 'none', borderRadius: 9999,
                padding: '16px 48px', fontSize: 18, fontWeight: 700,
                cursor: 'pointer', transition: 'transform 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              data-testid="cta-signup-btn"
            >
              join the hive
            </button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ background: NAVY, padding: '40px 24px 24px' }}>
        <div style={{ maxWidth: 1152, margin: '0 auto' }}>
          {/* Top row */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, paddingBottom: 24, borderBottom: `1px solid ${SLATE}` }}>
            {/* Text logo */}
            <span style={{ fontFamily: "'Playfair Display', serif", fontSize: 20 }}>
              <em style={{ color: GOLD }}>the</em>
              <span style={{ color: '#fff', marginLeft: 6 }}>Honey</span>
              <span style={{ color: GOLD, marginLeft: 4 }}>Groove</span>
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
              <Link to="/about" style={{ color: 'rgba(255,255,255,0.55)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-about-link">About</Link>
              <Link to="/faq" style={{ color: 'rgba(255,255,255,0.55)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-faq-link">FAQ</Link>
              <Link to="/terms" style={{ color: 'rgba(255,255,255,0.55)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-terms-link">Terms</Link>
              <Link to="/privacy" style={{ color: 'rgba(255,255,255,0.55)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-privacy-link">Privacy</Link>
              <Link to="/guidelines" style={{ color: 'rgba(255,255,255,0.55)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-guidelines-link">Guidelines</Link>
            </div>
          </div>

          {/* Copyright row */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, paddingTop: 20 }}>
            <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>
              &copy; 2026 the Honey Groove<sup style={{ fontSize: '0.6em' }}>&trade;</sup>. Made with love for vinyl collectors.
            </p>
            {/* Social links */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <a href="https://www.tiktok.com/@thehoneygroove?is_from_webapp=1&sender_device=pc" target="_blank" rel="noopener noreferrer" style={{ color: 'rgba(255,255,255,0.45)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-tiktok-link">TikTok</a>
              <a href="https://www.instagram.com/thehoneygroove" target="_blank" rel="noopener noreferrer" style={{ color: 'rgba(255,255,255,0.45)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-instagram-link">Instagram</a>
              <a href="https://discord.gg/rMZFGw6CPf" target="_blank" rel="noopener noreferrer" style={{ color: 'rgba(255,255,255,0.45)', textDecoration: 'none', fontSize: 13 }} className="hover:text-white transition-colors" data-testid="footer-discord-link">Discord</a>
            </div>
          </div>
        </div>
      </footer>

      {/* ── WAITLIST MODAL ── */}
      {waitlistOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 animate-fade-in" data-testid="waitlist-modal">
          <div style={{ background: CREAM, borderRadius: 20, padding: 40, maxWidth: 420, width: '90%', position: 'relative', boxShadow: '0 24px 64px rgba(0,0,0,0.25)', border: `1px solid #E5DBC880` }}>
            <button onClick={() => setWaitlistOpen(false)} style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', cursor: 'pointer', color: '#1F1F1F60' }} data-testid="waitlist-close-btn">
              <X className="w-5 h-5" />
            </button>
            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, color: '#1F1F1F', marginBottom: 12, textAlign: 'center' }}>closed beta</h3>
            <p style={{ fontSize: 14, color: '#1F1F1F80', marginBottom: 28, textAlign: 'center', lineHeight: 1.6 }}>
              the honey groove is currently in closed beta. join the waitlist to get early access.
            </p>
            <Button
              onClick={() => { setWaitlistOpen(false); navigate('/beta'); }}
              className="w-full rounded-full py-5 text-base font-medium"
              style={{ background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`, color: NAVY }}
              data-testid="waitlist-beta-btn"
            >
              join the waitlist 🐝
            </Button>
          </div>
        </div>
      )}

      {/* ── NEWSLETTER POPUP ── */}
      {popupOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 animate-fade-in" data-testid="newsletter-popup">
          <div style={{ background: CREAM, borderRadius: 20, padding: 40, maxWidth: 420, width: '90%', position: 'relative', boxShadow: '0 24px 64px rgba(0,0,0,0.25)', border: `1px solid #E5DBC880` }}>
            <button onClick={dismissPopup} style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', cursor: 'pointer', color: '#1F1F1F60' }} data-testid="popup-dismiss-btn">
              <X className="w-5 h-5" />
            </button>
            <h3 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, color: '#1F1F1F', marginBottom: 10, textAlign: 'center' }}>stay in the loop</h3>
            <p style={{ fontSize: 14, color: '#1F1F1F80', marginBottom: 24, textAlign: 'center', lineHeight: 1.6 }}>
              a weekly letter for collectors. new finds, community stories, and what's buzzing in the hive. no spam, just wax.
            </p>
            {popupSuccess ? (
              <p style={{ color: GOLD, fontWeight: 600, textAlign: 'center' }}>you're in! welcome to the hive 🍯</p>
            ) : (
              <div style={{ display: 'flex', gap: 8 }}>
                <Input
                  type="email"
                  placeholder="your email address"
                  value={popupEmail}
                  onChange={e => setPopupEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubscribe(popupEmail, setPopupLoading, setPopupSuccess)}
                  style={{ flex: 1, border: `1px solid #E5DBC8`, background: '#fff' }}
                  data-testid="popup-email-input"
                />
                <button
                  onClick={() => handleSubscribe(popupEmail, setPopupLoading, setPopupSuccess)}
                  disabled={popupLoading}
                  style={{
                    background: `linear-gradient(135deg, ${GOLD}, ${GOLD_LIGHT})`,
                    color: NAVY, border: 'none', borderRadius: 9999,
                    padding: '0 20px', fontSize: 14, fontWeight: 700,
                    cursor: popupLoading ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}
                  data-testid="popup-subscribe-btn"
                >
                  {popupLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'subscribe 🍯'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;
