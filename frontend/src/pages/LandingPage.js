import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Disc, Music2, ShoppingBag, Search, ArrowLeftRight, Share2, X, Loader2 } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';

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
    { icon: <Disc className="w-6 h-6" />, title: "Track Your Collection", description: "Add records with album art pulled from Discogs. Log every press, note conditions, and watch your collection grow — and appreciate in value." },
    { icon: <Music2 className="w-6 h-6" />, title: "Now Spinning", description: "Drop the needle, share the moment. Log your spin, pick a mood, and let your people know exactly what you're feeling right now." },
    { icon: <ShoppingBag className="w-6 h-6" />, title: "New Haul", description: "Record store day. Thrift score. eBay win. Show off every find to people who actually understand why it matters." },
    { icon: <Search className="w-6 h-6" />, title: "ISO", description: "Been hunting something for years? Post it. Get matched with collectors who have it and reach out directly." },
    { icon: <ArrowLeftRight className="w-6 h-6" />, title: "Trade", description: "Offer a record from your collection, add a sweetener if needed, and swap directly with collectors. No middleman. Just the community." },
    { icon: <Share2 className="w-6 h-6" />, title: "Shareable Graphics", description: "Generate beautiful Now Spinning and Haul cards built for Instagram. One tap, ready to post." },
  ];

  return (
    <div className="min-h-screen bg-honey-cream relative">
      <HoneycombPattern />

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 md:px-8 pt-16">
          <div className="text-center max-w-4xl mx-auto">
            {/* Logo */}
            <div className="flex justify-center mb-2">
              <img
                src="/logo-drip.png"
                alt="the Honey Groove"
                className="w-[85vw] max-w-[520px] md:max-w-[560px] lg:max-w-[600px]"
              />
            </div>

            {/* Bee bridge */}
            <p className="text-[28px] mb-4" style={{ color: 'rgba(200,134,26,0.6)' }}>🐝</p>

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

      {/* Features Section */}
      <section className="py-20 bg-white/50 relative">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-4">
              built for the <span className="text-honey-amber italic">obsessed.</span>
            </h2>
            <p className="text-base md:text-lg text-vinyl-black/70 max-w-xl mx-auto">
              The Honey Groove is designed by collectors, for collectors. here's what makes our hive special.
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
              <p className="text-sm text-vinyl-black/50">
                &copy; 2026 the Honey Groove. Made with love for vinyl collectors.
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
