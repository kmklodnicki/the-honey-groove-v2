import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Mail, ArrowLeft } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

const AboutPage = () => {
  usePageTitle('About');
  return (
  <div className="min-h-screen bg-honey-cream">
    <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="about-page">
      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors mb-10"
        data-testid="about-back-link"
      >
        <ArrowLeft className="w-4 h-4" /> back home
      </Link>

      {/* Header */}
      <h1 className="font-heading text-4xl sm:text-5xl text-vinyl-black mb-2">
        About the Honey Groove
      </h1>
      <p className="text-honey-amber font-heading text-lg mb-12">
        built by a collector. for collectors.
      </p>

      {/* Story */}
      <div className="space-y-6 text-vinyl-black/80 leading-relaxed">
        <p>
          I started collecting vinyl in 2022 and haven't stopped since.
        </p>
        <p>
          What began as a few records quickly turned into hundreds. A U-Turn Orbit Custom,
          a Blue Ortofon needle, a Pluto 2 preamp, Edifier speakers, and a growing stack of
          records that somehow keeps finding more shelf space.
        </p>
        <p>
          The more obsessed I became, the more I noticed that nothing online actually fit the
          way collectors live. Discogs is a database. Reddit is chaotic. Instagram doesn't care
          about the details. There was no place that felt like home for people who care about
          the music, the hunt, the haul, and the community all at once.
        </p>
        <p className="font-medium text-vinyl-black">
          So I built it.
        </p>
        <p>
          The Honey Groove is the social app I always wanted. A place to track what you own,
          share what you're spinning, post the finds that made your week, hunt down the records
          you've been chasing for years, and trade directly with people who get it.
        </p>
        <p className="text-vinyl-black font-medium italic">
          It's for the ones who understand why a record matters.
        </p>
      </div>

      {/* Signature */}
      <div className="mt-12 pt-8 border-t border-honey/30">
        <p className="text-vinyl-black/70 text-sm">
          — <strong className="text-vinyl-black">Katie</strong>, founder
        </p>
        <p className="text-honey-amber text-sm mt-1">@katieintheafterglow</p>
      </div>

      {/* Find us */}
      <div className="mt-14 bg-honey/10 rounded-2xl p-8 border border-honey/20" data-testid="about-find-us">
        <h2 className="font-heading text-xl text-vinyl-black mb-5">find us</h2>
        <div className="space-y-3">
          <a
            href="https://instagram.com/thehoneygroove"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 text-sm text-vinyl-black/70 hover:text-honey-amber transition-colors group"
            data-testid="about-instagram"
          >
            <Instagram className="w-5 h-5 text-honey-amber group-hover:scale-110 transition-transform" />
            Instagram: @thehoneygroove
          </a>
          <a
            href="https://tiktok.com/@thehoneygroove"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 text-sm text-vinyl-black/70 hover:text-honey-amber transition-colors group"
            data-testid="about-tiktok"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-honey-amber group-hover:scale-110 transition-transform" fill="currentColor">
              <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.34-6.34V8.73a8.19 8.19 0 004.76 1.52v-3.4a4.85 4.85 0 01-1-.16z"/>
            </svg>
            TikTok: @thehoneygroove
          </a>
          <a
            href="mailto:hello@thehoneygroove.com"
            className="flex items-center gap-3 text-sm text-vinyl-black/70 hover:text-honey-amber transition-colors group"
            data-testid="about-email"
          >
            <Mail className="w-5 h-5 text-honey-amber group-hover:scale-110 transition-transform" />
            hello@thehoneygroove.com
          </a>
        </div>
      </div>
    </div>
  </div>
  );
};

export default AboutPage;
