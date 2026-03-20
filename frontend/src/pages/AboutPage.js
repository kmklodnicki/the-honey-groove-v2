import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, DollarSign, Shield, Music2, TrendingUp } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import SEOHead from '../components/SEOHead';

const FOUNDER_PHOTO = "https://customer-assets.emergentagent.com/job_7bde1943-8e16-4fbd-a255-24d1bbe2a425/artifacts/kbi8p181_KatieKlodnicki%20About%20Me.png";

const AboutPage = () => {
  usePageTitle('About');
  return (
    <div className="min-h-screen bg-honey-cream">
      <SEOHead
        title="About The Honey Groove — Built by a Collector, for Collectors"
        description="The Honey Groove is a social vinyl tracking platform built by a collector, for collectors. Track your collection, discover pressings, and connect with collectors worldwide."
        url="/about"
      />
      <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-12" data-testid="about-page">
        {/* Back link */}
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors mb-10" data-testid="about-back-link">
          <ArrowLeft className="w-4 h-4" /> back home
        </Link>

        {/* Header */}
        <h1 className="font-heading text-4xl sm:text-5xl text-vinyl-black mb-2">About the Honey Groove<sup style={{ fontSize: '0.6em' }}>&trade;</sup></h1>
        <p className="text-honey-amber font-heading text-lg mb-10">built by a collector. for collectors.</p>

        {/* Founder Photo */}
        <div className="flex justify-center mb-12" data-testid="founder-photo">
          <div className="w-[280px] h-[280px] rounded-2xl overflow-hidden border-2 border-honey/30 shadow-lg">
            <img
              src={FOUNDER_PHOTO}
              alt="Katie Klodnicki, founder of the Honey Groove"
              className="w-full h-full object-cover object-top"
            />
          </div>
        </div>

        {/* Story */}
        <div className="space-y-6 text-vinyl-black/80 leading-relaxed">
          <p>I started collecting vinyl in 2022 and haven't stopped since.</p>
          <p>What began as a few records turned into hundreds. A U-Turn Orbit Custom, a Blue Ortofon needle, a Pluto 2 preamp, Edifier speakers, and a growing stack that somehow always finds more shelf space.</p>
          <p>The more obsessed I became, the more I noticed that nothing online actually fit the way collectors live. The big databases are databases. Reddit is chaotic. Instagram was built for everyone, which means it was built for no one. There was no place that felt like home for people who care about the music, the hunt, the haul, and the community all at once.</p>
          <p className="font-medium text-vinyl-black">So I built it.</p>
          <p>The Honey Groove is the app I always wanted. Track what you own, share what you're spinning, post the finds that made your week, hunt down records you've been chasing for years, and trade directly with people who get it. Every trade protected by a Mutual Hold so you never have to trust a stranger on faith alone.</p>
          <p>It started as a personal problem. It became something I think a lot of us needed.</p>
          <p className="text-vinyl-black font-medium italic">If you collect vinyl · casually, obsessively, or somewhere in between · you belong here.</p>
        </div>

        {/* Signature */}
        <div className="mt-12 pt-8 border-t border-honey/30">
          <p className="text-vinyl-black/70 text-sm">· <strong className="text-vinyl-black">Katie Klodnicki</strong>, founder</p>
          <p className="text-honey-amber text-sm mt-1">@katieintheafterglow</p>
        </div>

        {/* What makes us different */}
        <div className="mt-16">
          <h2 className="font-heading text-2xl text-vinyl-black mb-8">What makes the Honey Groove different</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4" data-testid="about-features-grid">
            <FeatureCard
              icon={<DollarSign className="w-5 h-5" />}
              title="Lower fees."
              body="6% on completed sales. Lower than every major competitor, lower than every other marketplace you're selling on right now."
            />
            <FeatureCard
              icon={<Shield className="w-5 h-5" />}
              title="Mutual Hold trades."
              body="Every trade requires both parties to put up a hold equal to the estimated record value. Fully reversed on confirmed delivery. No risk, no blind trust, no getting burned."
            />
            <FeatureCard
              icon={<Music2 className="w-5 h-5" />}
              title="Built for the culture."
              body="Weekly Wax reports, daily prompts, mood-based sharing, collector bingo, mood boards. This isn't a spreadsheet with social features. It's a place that actually reflects how collectors think and feel about music."
            />
            <FeatureCard
              icon={<TrendingUp className="w-5 h-5" />}
              title="Your collection, valued."
              body="Every record in your Vault shows its current market value. Watch your collection grow in more ways than one."
            />
          </div>
        </div>

        {/* CTA */}
        <div className="mt-14 text-center" data-testid="about-cta">
          <p className="text-vinyl-black/60 text-sm mb-4">The Honey Groove is in closed beta.</p>
          <p className="text-vinyl-black/60 text-sm mb-6">
            Founding members get early access, a permanent badge, and a direct line to me while we build.
          </p>
          <Link
            to="/beta"
            className="inline-flex items-center justify-center px-8 py-3.5 bg-[#E8A820] hover:bg-[#d49a1a] text-[#1E2A3A] font-medium text-base rounded-full transition-colors shadow-sm"
            data-testid="about-join-waitlist-btn"
          >
            request your invite 🐝
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 border-t border-honey/20">
        <div className="max-w-2xl mx-auto px-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <Link to="/">
              <img src="/logo-wordmark.png" alt="the Honey Groove" className="h-8 opacity-60" />
            </Link>
            <div className="flex items-center gap-6">
              <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">FAQ</Link>
              <Link to="/terms" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Terms</Link>
              <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Privacy</Link>
              <Link to="/guidelines" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Guidelines</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

const FeatureCard = ({ icon, title, body }) => (
  <div className="bg-white/60 border border-honey/20 rounded-2xl p-6 space-y-2" data-testid={`about-feature-${title.split('.')[0].toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="w-9 h-9 rounded-full bg-honey/15 flex items-center justify-center text-honey-amber">{icon}</div>
    <h3 className="font-heading text-base text-vinyl-black">{title}</h3>
    <p className="text-sm text-vinyl-black/60 leading-relaxed">{body}</p>
  </div>
);

export default AboutPage;
