import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Disc, Users, Music2, Share2, TrendingUp, Hexagon } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  // Honeycomb pattern component
  const HoneycombPattern = () => (
    <div className="absolute inset-0 opacity-5 pointer-events-none honeycomb-pattern" />
  );

  // Bee icon component
  const BeeIcon = ({ className = "w-6 h-6" }) => (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1F1F1F"/>
      <ellipse cx="12" cy="14" rx="3.5" ry="2.5" fill="#F4B942"/>
      <circle cx="12" cy="8" r="3" fill="#1F1F1F"/>
      <ellipse cx="7" cy="7" rx="2" ry="3" fill="#1F1F1F" opacity="0.4" transform="rotate(-30 7 7)"/>
      <ellipse cx="17" cy="7" rx="2" ry="3" fill="#1F1F1F" opacity="0.4" transform="rotate(30 17 7)"/>
    </svg>
  );

  return (
    <div className="min-h-screen bg-honey-cream relative">
      <HoneycombPattern />
      
      {/* Hero Section */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-20 right-10 animate-float">
          <BeeIcon className="w-8 h-8 opacity-30" />
        </div>
        <div className="absolute bottom-40 left-20 animate-float" style={{ animationDelay: '1s' }}>
          <BeeIcon className="w-6 h-6 opacity-20" />
        </div>
        
        <div className="max-w-6xl mx-auto px-4 md:px-8 pt-16">
          <div className="text-center max-w-4xl mx-auto">
            {/* Logo */}
            <div className="flex justify-center mb-8">
              <div className="flex items-center gap-3 bg-white/50 backdrop-blur-sm px-6 py-3 rounded-full border border-honey/30">
                <div className="w-12 h-12 bg-honey rounded-full flex items-center justify-center">
                  <Disc className="w-7 h-7 text-vinyl-black" />
                </div>
                <span className="font-heading text-3xl text-vinyl-black">HoneyGroove</span>
              </div>
            </div>

            {/* Tagline */}
            <h1 className="font-heading text-5xl md:text-7xl text-vinyl-black tracking-tight mb-6 animate-fade-in">
              The Social Network for{' '}
              <span className="text-honey-amber italic">Vinyl Collectors</span>
            </h1>

            <p className="text-lg md:text-xl text-vinyl-black/70 mb-10 max-w-2xl mx-auto animate-slide-up">
              Track your records, log your spins, share your hauls, and connect with fellow collectors in a warm, welcoming community.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Button 
                onClick={() => navigate('/signup')}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full px-8 py-6 text-lg font-medium hover:scale-105 transition-transform"
                data-testid="hero-signup-btn"
              >
                Start Your Collection
              </Button>
              <Button 
                onClick={() => navigate('/explore')}
                variant="outline"
                className="border-2 border-vinyl-black rounded-full px-8 py-6 text-lg hover:bg-vinyl-black hover:text-white transition-colors"
                data-testid="hero-explore-btn"
              >
                Explore The Hive
              </Button>
            </div>
          </div>

          {/* Hero Image/Visual */}
          <div className="mt-16 relative">
            <div className="flex justify-center gap-4 md:gap-8">
              {/* Vinyl Record Visual */}
              <div className="relative w-48 h-48 md:w-64 md:h-64 animate-spin-slow">
                <div className="absolute inset-0 rounded-full bg-vinyl-black shadow-vinyl"></div>
                <div className="absolute inset-4 rounded-full bg-gradient-to-br from-gray-800 to-gray-900"></div>
                {[...Array(8)].map((_, i) => (
                  <div 
                    key={i}
                    className="absolute rounded-full border border-gray-700"
                    style={{
                      top: `${15 + i * 5}%`,
                      left: `${15 + i * 5}%`,
                      right: `${15 + i * 5}%`,
                      bottom: `${15 + i * 5}%`,
                    }}
                  />
                ))}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 md:w-20 md:h-20 rounded-full bg-honey flex items-center justify-center">
                  <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-honey-amber flex items-center justify-center">
                    <div className="w-3 h-3 rounded-full bg-vinyl-black"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white/50 relative">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-4">
              Everything You Need to <span className="text-honey-amber italic">Groove</span>
            </h2>
            <p className="text-vinyl-black/70 max-w-xl mx-auto">
              HoneyGroove is designed by collectors, for collectors. Here's what makes our hive special.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature Cards */}
            <FeatureCard 
              icon={<Disc className="w-6 h-6" />}
              title="Track Your Collection"
              description="Add records with album art from Discogs. Keep notes, track spins, and watch your collection grow."
            />
            <FeatureCard 
              icon={<Music2 className="w-6 h-6" />}
              title="Log Your Spins"
              description="Record every time you drop the needle. Build your listening history and discover your favorites."
            />
            <FeatureCard 
              icon={<Users className="w-6 h-6" />}
              title="Connect in The Hive"
              description="Follow fellow collectors, see what they're spinning, and discover new music together."
            />
            <FeatureCard 
              icon={<TrendingUp className="w-6 h-6" />}
              title="Weekly Summaries"
              description="Get your HoneyGroove Weekly report with top artists, albums, and your listening mood."
            />
            <FeatureCard 
              icon={<Share2 className="w-6 h-6" />}
              title="Shareable Graphics"
              description="Create beautiful Now Spinning and Haul cards to share on Instagram and social media."
            />
            <FeatureCard 
              icon={<Hexagon className="w-6 h-6" />}
              title="Buzzing Now"
              description="See what's trending in the community. Discover what other collectors are spinning."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <div className="bg-honey/20 rounded-3xl p-12 border border-honey/30 relative overflow-hidden">
            <div className="absolute top-4 right-8 animate-float">
              <BeeIcon className="w-10 h-10 opacity-30" />
            </div>
            <h2 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-4">
              Ready to Join The Hive?
            </h2>
            <p className="text-vinyl-black/70 mb-8 max-w-lg mx-auto">
              Start tracking your vinyl collection today and connect with thousands of collectors worldwide.
            </p>
            <Button 
              onClick={() => navigate('/signup')}
              className="bg-vinyl-black text-white hover:bg-vinyl-black/90 rounded-full px-10 py-6 text-lg font-medium hover:scale-105 transition-transform"
              data-testid="cta-signup-btn"
            >
              Create Free Account
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-honey/20">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-honey rounded-full flex items-center justify-center">
                <Disc className="w-5 h-5 text-vinyl-black" />
              </div>
              <span className="font-heading text-xl text-vinyl-black">HoneyGroove</span>
            </div>
            <p className="text-sm text-vinyl-black/50">
              © 2024 HoneyGroove. Made with love for vinyl collectors.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Feature Card Component
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
