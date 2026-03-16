import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Disc, Music2, ShoppingBag, Search, ArrowLeftRight, Share2, X, Loader2, Shield, CheckCircle2, ArrowRight } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import SEOHead from '../components/SEOHead';

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

  const HoneycombPattern = () => (
    <div className="absolute inset-0 opacity-5 pointer-events-none honeycomb-pattern" />
  );

  const features = [
    { icon: <Disc className="w-6 h-6" />, title: "Track Your Vault", description: "Know exactly what you own and what it's worth. Every record in your vault shows its current Discogs market value, updated regularly." },
    { icon: <Music2 className="w-6 h-6" />, title: "Now Spinning", description: "Drop the needle, share the moment. Log your spin, pick a mood, and let the hive know what's on the turntable right now." },
    { icon: <ShoppingBag className="w-6 h-6" />, title: "The Honeypot", description: "A peer-to-peer marketplace where collectors buy, sell, and trade directly. Lower fees than any major vinyl marketplace \u2014 because you should keep more of what your records are worth." },
    { icon: <Search className="w-6 h-6" />, title: "ISO", description: "Post what you've been hunting. Get matched with collectors who have it. We notify you the moment your record appears \u2014 so you never miss it again." },
    { icon: <ArrowLeftRight className="w-6 h-6" />, title: "Trade with Confidence", description: "Every trade protected by a Mutual Hold. Both parties put up a hold equal to the estimated record value. Fully reversed on delivery. No risk, no blind trust." },
    { icon: <Share2 className="w-6 h-6" />, title: "Your Week in Wax", description: "Every Sunday a full breakdown of your listening week \u2014 top artists, moods, eras, and a one-line summary of who you were as a listener. Shareable to Instagram Stories in one tap." },
  ];

  return (
    <div className="min-h-screen bg-honey-cream relative">
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
      <HoneycombPattern />

      {/* Hero Section */}
      <section className="relative pb-24 overflow-hidden pt-[120px]">
        {/* Gold line · top edge */}
        <div className="absolute top-0 left-0 w-screen z-10" style={{ height: '2px', background: 'linear-gradient(90deg, #D4A017, #E8B923, #D4A017)' }} />
        {/* Honey drip · tiled video strip pinned flush to top */}
        <div
          className="absolute top-0 left-0 w-screen overflow-hidden z-0 flex"
          style={{ height: '120px', marginTop: '-1px', backgroundColor: '#FEF6E6' }}
          data-testid="hero-drip"
        >
          {[0,1,2].map(i => {
            const mask = i === 0
              ? 'linear-gradient(to right, black 92%, transparent 100%)'
              : i === 2
                ? 'linear-gradient(to left, black 92%, transparent 100%)'
                : 'linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%)';
            return (
            <video
              key={i}
              autoPlay
              loop
              muted
              playsInline
              disablePictureInPicture
              poster="/honey-drip.png"
              className="block h-full flex-shrink-0"
              style={{
                width: 'calc(100vw / 3 + 10px)',
                marginLeft: i === 0 ? 0 : '-5px',
                marginRight: i === 2 ? 0 : '-5px',
                objectFit: 'cover',
                objectPosition: 'top center',
                mixBlendMode: 'multiply',
                WebkitMaskImage: mask,
                maskImage: mask,
              }}
              {...(i === 0 ? { 'data-testid': 'hero-drip-video' } : {})}
            >
              <source src="/honey-drip.mp4" type="video/mp4" />
            </video>
            );
          })}
        </div>
        {/* Gold line · bottom of drip */}
        <div className="absolute left-0 w-screen z-10" style={{ top: '120px', height: '2px', background: 'linear-gradient(90deg, #D4A017, #E8B923, #D4A017)' }} />

        {/* Organic hero assets · desktop only */}
        <img
          src="/hero-left.png"
          alt=""
          aria-hidden="true"
          className="hidden lg:block absolute pointer-events-none"
          style={{
            left: 0,
            top: '25%',
            width: '20vw',
            objectFit: 'contain',
            willChange: 'transform',
            zIndex: 5,
          }}
          data-testid="hero-asset-left"
        />
        <img
          src="/hero-right.png"
          alt=""
          aria-hidden="true"
          className="hidden lg:block absolute pointer-events-none"
          style={{
            right: 0,
            top: 0,
            width: '20vw',
            objectFit: 'contain',
            willChange: 'transform',
            zIndex: 5,
          }}
          data-testid="hero-asset-right"
        />

        <div className="max-w-6xl mx-auto px-4 md:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            {/* Logo wordmark · below the drip */}
            <div className="flex justify-center pt-[40px] pb-[24px] relative z-10">
              <img
                src="/logo-wordmark-clean.png"
                alt="the Honey Groove"
                className="w-[85vw] max-w-[520px]"
                data-testid="hero-logo"
              />
            </div>

            {/* Headline */}
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl text-vinyl-black tracking-tight mb-6 animate-fade-in">
              the vinyl social club,{' '}
              <span className="text-honey-amber italic">finally.</span>
            </h1>

            {/* Sub-copy */}
            <p className="text-base md:text-lg text-vinyl-black/70 mb-10 max-w-2xl mx-auto animate-slide-up">
              track your records, share your hauls, hunt down your ISO, and trade with people who get it.
            </p>

            {/* CTA */}
            <div className="flex flex-col items-center gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Button
                onClick={() => setWaitlistOpen(true)}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full px-8 py-6 text-lg font-medium hover:scale-105 transition-transform"
                data-testid="hero-signup-btn"
              >
                join the hive
              </Button>
              <Link
                to="/login"
                className="text-sm text-vinyl-black/60 hover:text-honey-amber transition-colors"
                data-testid="hero-login-link"
              >
                already a member? sign in &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Gold separator line */}
      <div className="w-full" style={{ height: '2px', background: 'linear-gradient(90deg, #D4A017, #E8B923, #D4A017)' }} />

      {/* SECTION 1 · Stats Strip */}
      <section className="py-12 md:py-16 relative" style={{ background: '#F0E8D8' }} data-testid="stats-strip">
        <div className="max-w-5xl mx-auto px-4 md:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-0">
            {[
              { num: '6%', label: 'transaction fee. lower than everywhere else.' },
              { num: 'Free', label: 'to join. always.' },
              { num: '100%', label: 'of trade holds reversed on confirmed delivery.' },
              { num: '\u2728', label: 'Limited Founding Members. join the hive.' },
            ].map((stat, i) => (
              <div key={i} className={`text-center ${i < 3 ? 'lg:border-r lg:border-[#C8861A]/20' : ''}`} data-testid={`stat-${i}`}>
                <div className="text-5xl md:text-[64px] font-bold leading-none mb-3" style={{ fontFamily: "'Playfair Display', serif", color: '#996012' }}>
                  {stat.num}
                </div>
                <p className="text-sm md:text-lg italic max-w-[200px] mx-auto leading-snug" style={{ fontFamily: "'Cormorant Garamond', serif", color: '#8A6B4A' }}>
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 2 · Mutual Hold Feature Spotlight */}
      <section className="py-20 md:py-28 bg-honey-cream relative" data-testid="mutual-hold-spotlight">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left column · Text */}
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] uppercase mb-4" style={{ color: '#C8861A' }}>
                TRADE WITH CONFIDENCE
              </p>
              <h2 className="text-3xl sm:text-4xl lg:text-[52px] lg:leading-[1.1] font-bold text-vinyl-black mb-6" style={{ fontFamily: "'Playfair Display', serif" }}>
                Both parties protected.{' '}
                <span className="italic text-honey-amber">Every single trade.</span>
              </h2>
              <p className="text-base md:text-xl leading-relaxed mb-8" style={{ fontFamily: "'Cormorant Garamond', serif", color: '#8A6B4A' }}>
                Every trade on the Honey Groove requires a Mutual Hold. Both collectors put up a hold equal to the estimated value of the records being traded. The hold is fully reversed within 48 hours of confirmed delivery on both sides. Nobody walks away ahead by scamming. The math makes it impossible.
              </p>
              <Link to="/faq#trades" className="inline-flex items-center gap-2 text-sm font-medium text-[#C8861A] hover:text-[#996012] transition-colors" data-testid="learn-hold-link">
                Learn how it works <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            {/* Right column · Visual diagram */}
            <div className="flex justify-center">
              <div className="w-full max-w-[400px] rounded-3xl border-2 border-[#C8861A]/15 bg-white/60 p-8 md:p-10" data-testid="hold-diagram">
                <div className="flex items-center justify-between mb-8">
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#F0E8D8] border border-[#C8861A]/20 flex items-center justify-center mx-auto mb-2">
                      <Disc className="w-7 h-7 text-[#C8861A]" />
                    </div>
                    <p className="text-xs font-medium text-vinyl-black/70">Collector A</p>
                  </div>
                  <div className="flex-1 flex flex-col items-center gap-1 px-2">
                    <div className="flex items-center gap-1 text-[#C8861A]/50">
                      <div className="h-px flex-1 bg-[#C8861A]/20" />
                      <ArrowLeftRight className="w-4 h-4 shrink-0" />
                      <div className="h-px flex-1 bg-[#C8861A]/20" />
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#F0E8D8] border border-[#C8861A]/20 flex items-center justify-center mx-auto mb-2">
                      <Disc className="w-7 h-7 text-[#C8861A]" />
                    </div>
                    <p className="text-xs font-medium text-vinyl-black/70">Collector B</p>
                  </div>
                </div>
                <div className="text-center mb-6">
                  <div className="inline-flex items-center gap-2 bg-[#E8A820]/10 border border-[#C8861A]/20 rounded-full px-5 py-2.5">
                    <Shield className="w-5 h-5 text-[#C8861A]" />
                    <span className="text-sm font-semibold text-[#996012]">Hold Active</span>
                  </div>
                </div>
                <div className="border-t border-dashed border-[#C8861A]/20 pt-5">
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-[#C8861A]" />
                    <span className="text-sm font-medium text-[#C8861A]">Delivery Confirmed · Holds Released</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3 · Fee Comparison */}
      <section className="py-16 md:py-20 relative" style={{ background: '#F0E8D8' }} data-testid="fee-comparison">
        <div className="max-w-xl mx-auto px-4 md:px-8 text-center">
          <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-3">
            Finally. A marketplace that's <span className="text-honey-amber italic">on your side.</span>
          </h2>
          <p className="text-base md:text-lg italic mb-10" style={{ fontFamily: "'Cormorant Garamond', serif", color: '#8A6B4A' }}>
            we charge less so you keep more.
          </p>
          <div className="max-w-[480px] mx-auto rounded-2xl overflow-hidden border border-[#C8861A]/15 bg-white/80" data-testid="fee-table">
            {[
              { name: 'eBay', fee: '12.9%', highlight: false },
              { name: 'Discogs', fee: '8%', highlight: false },
              { name: 'The Honey Groove\u2122', fee: '6%', highlight: true },
            ].map((row) => (
              <div
                key={row.name}
                className={`flex items-center justify-between px-6 py-4 ${
                  row.highlight
                    ? 'bg-[#E8A820]/15 border-l-[3px] border-l-[#E8A820] font-bold text-vinyl-black'
                    : 'text-vinyl-black/50 border-b border-[#C8861A]/10'
                }`}
                data-testid={`fee-row-${row.name.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <span className={row.highlight ? 'text-base' : 'text-sm'}>{row.name}</span>
                <span className={row.highlight ? 'text-xl text-[#996012]' : 'text-sm'}>{row.fee}</span>
              </div>
            ))}
          </div>
          <p className="text-sm italic mt-6" style={{ fontFamily: "'Cormorant Garamond', serif", color: '#8A6B4A' }}>
            fees apply to completed sales only. trades with no sweetener are always free.
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white/50 relative">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-4">
              built for the <span className="text-honey-amber italic">obsessed.</span>
            </h2>
            <p className="text-base md:text-lg text-vinyl-black/70 max-w-xl mx-auto">
              The Honey Groove is designed by collectors, for collectors. Here's what makes our hive different.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <FeatureCard key={f.title} icon={f.icon} title={f.title} description={f.description} />
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-16 relative" data-testid="newsletter-section">
        <div className="max-w-xl mx-auto px-4 md:px-8 text-center">
          <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-3">
            stay in the loop
          </h2>
          <p className="text-sm md:text-base text-vinyl-black/60 mb-8 leading-relaxed">
            a weekly letter for collectors. new finds, community stories, and what's buzzing in the hive. no spam, just wax.
          </p>
          {nlSuccess ? (
            <p className="text-amber-700 font-medium text-lg">you're in! welcome to the hive 🍯</p>
          ) : (
            <div className="flex gap-2 max-w-md mx-auto">
              <Input
                type="email"
                placeholder="your email address"
                value={nlEmail}
                onChange={e => setNlEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubscribe(nlEmail, setNlLoading, setNlSuccess)}
                className="border-amber-200 bg-white flex-1"
                data-testid="newsletter-email-input"
              />
              <Button
                onClick={() => handleSubscribe(nlEmail, setNlLoading, setNlSuccess)}
                disabled={nlLoading}
                className="bg-amber-500 hover:bg-amber-600 text-white rounded-full px-6 shrink-0"
                data-testid="newsletter-subscribe-btn"
              >
                {nlLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'subscribe 🍯'}
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <div className="bg-honey/20 rounded-3xl p-12 border border-honey/30 relative overflow-hidden">
            <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-4">
              Ready to Join The Hive?
            </h2>
            <p className="text-base md:text-lg text-vinyl-black/70 mb-8 max-w-lg mx-auto">
              you've been waiting for this. so have we.
            </p>
            <Button
              onClick={() => setWaitlistOpen(true)}
              className="bg-vinyl-black text-white hover:bg-vinyl-black/90 rounded-full px-10 py-6 text-lg font-medium hover:scale-105 transition-transform"
              data-testid="cta-signup-btn"
            >
              join the hive
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-honey/20">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <img
              src="/logo-wordmark.png"
              alt="the Honey Groove"
              className="w-[180px] md:w-[200px]"
            />
            <div className="flex items-center gap-6">
              <Link to="/about" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors" data-testid="footer-about-link">About</Link>
              <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors" data-testid="footer-faq-link">FAQ</Link>
              <Link to="/terms" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors" data-testid="footer-terms-link">Terms</Link>
              <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors" data-testid="footer-privacy-link">Privacy</Link>
              <p className="text-sm text-vinyl-black/50">
                &copy; 2026 the Honey Groove<sup style={{ fontSize: '0.6em' }}>&trade;</sup>. Made with love for vinyl collectors.
              </p>
            </div>
          </div>
        </div>
      </footer>

      {/* Waitlist Modal */}
      {waitlistOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 animate-fade-in" data-testid="waitlist-modal">
          <div className="bg-honey-cream rounded-2xl p-8 max-w-md mx-4 relative shadow-2xl border border-amber-200/50">
            <button onClick={() => setWaitlistOpen(false)} className="absolute top-3 right-3 text-vinyl-black/40 hover:text-vinyl-black" data-testid="waitlist-close-btn">
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-heading text-2xl text-vinyl-black mb-3 text-center">closed beta</h3>
            <p className="text-sm text-vinyl-black/60 mb-6 text-center leading-relaxed">
              the honey groove is currently in closed beta. join the waitlist to get early access.
            </p>
            <Button
              onClick={() => { setWaitlistOpen(false); navigate('/beta'); }}
              className="w-full bg-honey text-vinyl-black hover:bg-honey-amber rounded-full py-5 text-base font-medium"
              data-testid="waitlist-beta-btn"
            >
              join the waitlist 🐝
            </Button>
          </div>
        </div>
      )}

      {/* Newsletter Popup */}
      {popupOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 animate-fade-in" data-testid="newsletter-popup">
          <div className="bg-honey-cream rounded-2xl p-8 max-w-md mx-4 relative shadow-2xl border border-amber-200/50">
            <button onClick={dismissPopup} className="absolute top-3 right-3 text-vinyl-black/40 hover:text-vinyl-black" data-testid="popup-dismiss-btn">
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-heading text-2xl text-vinyl-black mb-2 text-center">stay in the loop</h3>
            <p className="text-sm text-vinyl-black/60 mb-6 text-center leading-relaxed">
              a weekly letter for collectors. new finds, community stories, and what's buzzing in the hive. no spam, just wax.
            </p>
            {popupSuccess ? (
              <p className="text-amber-700 font-medium text-center">you're in! welcome to the hive 🍯</p>
            ) : (
              <div className="flex gap-2">
                <Input
                  type="email"
                  placeholder="your email address"
                  value={popupEmail}
                  onChange={e => setPopupEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubscribe(popupEmail, setPopupLoading, setPopupSuccess)}
                  className="border-amber-200 bg-white flex-1"
                  data-testid="popup-email-input"
                />
                <Button
                  onClick={() => handleSubscribe(popupEmail, setPopupLoading, setPopupSuccess)}
                  disabled={popupLoading}
                  className="bg-amber-500 hover:bg-amber-600 text-white rounded-full px-5 shrink-0"
                  data-testid="popup-subscribe-btn"
                >
                  {popupLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'subscribe 🍯'}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const FeatureCard = ({ icon, title, description }) => (
  <div className="honey-card p-6 hover-lift" data-testid={`feature-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="w-12 h-12 bg-honey/30 rounded-xl flex items-center justify-center mb-4 text-honey-amber">
      {icon}
    </div>
    <h3 className="font-heading text-xl text-vinyl-black mb-2">{title}</h3>
    <p className="text-vinyl-black/70 text-sm">{description}</p>
  </div>
);

export default LandingPage;
