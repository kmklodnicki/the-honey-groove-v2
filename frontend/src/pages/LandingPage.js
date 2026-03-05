import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Disc, Music2, ShoppingBag, Search, ArrowLeftRight, Share2 } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

const LandingPage = () => {
  usePageTitle();
  const navigate = useNavigate();

  const HoneycombPattern = () => (
    <div className="absolute inset-0 opacity-5 pointer-events-none honeycomb-pattern" />
  );

  const features = [
    {
      icon: <Disc className="w-6 h-6" />,
      title: "Track Your Collection",
      description: "Add records with album art pulled from Discogs. Log every press, note conditions, and watch your collection grow — and appreciate in value.",
    },
    {
      icon: <Music2 className="w-6 h-6" />,
      title: "Now Spinning",
      description: "Drop the needle, share the moment. Log your spin, pick a mood, and let your people know exactly what you're feeling right now.",
    },
    {
      icon: <ShoppingBag className="w-6 h-6" />,
      title: "New Haul",
      description: "Record store day. Thrift score. eBay win. Show off every find to people who actually understand why it matters.",
    },
    {
      icon: <Search className="w-6 h-6" />,
      title: "ISO",
      description: "Been hunting something for years? Post it. Get matched with collectors who have it and reach out directly.",
    },
    {
      icon: <ArrowLeftRight className="w-6 h-6" />,
      title: "Trade",
      description: "Offer a record from your collection, add a sweetener if needed, and swap directly with collectors. No middleman. Just the community.",
    },
    {
      icon: <Share2 className="w-6 h-6" />,
      title: "Shareable Graphics",
      description: "Generate beautiful Now Spinning and Haul cards built for Instagram. One tap, ready to post.",
    },
  ];

  return (
    <div className="min-h-screen bg-honey-cream relative">
      <HoneycombPattern />

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 md:px-8 pt-16">
          <div className="text-center max-w-4xl mx-auto">
            {/* Logo */}
            <div className="flex justify-center mb-14 md:mb-16">
              <img
                src="/logo-drip.png"
                alt="the Honey Groove"
                className="w-[85vw] max-w-[520px] md:max-w-[560px] lg:max-w-[600px]"
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
                onClick={() => navigate('/signup')}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full px-8 py-6 text-lg font-medium hover:scale-105 transition-transform"
                data-testid="hero-signup-btn"
              >
                Start Your Collection
              </Button>
              <Link
                to="/explore"
                className="text-sm text-vinyl-black/60 hover:text-honey-amber transition-colors"
                data-testid="hero-explore-link"
              >
                or explore the hive &rarr;
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
              onClick={() => navigate('/signup')}
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
              className="h-12"
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
