import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import SEOHead from '../components/SEOHead';

const PrivacyPage = () => {
  usePageTitle('Privacy Policy');
  return (
    <div className="min-h-screen bg-honey-cream">
      <SEOHead
        title="Privacy Policy"
        description="Privacy Policy for The Honey Groove vinyl social platform. Learn how we protect your data."
        url="/privacy"
      />
      <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="privacy-page">
        <h1 className="font-heading text-4xl text-vinyl-black mb-2">Privacy Policy</h1>
        <p className="text-muted-foreground mb-10">Last updated March 2026</p>

        <Section title="What We Collect">
          <P>When you create an account we collect your email address, username, and password (stored securely as a hash). You may optionally provide your name, bio, location, favorite genre, and profile photo. When you use the platform we collect data about your collection, spins, posts, trades, and marketplace activity. We collect basic usage data through Google Analytics including pages visited and features used.</P>
        </Section>

        <Section title="How We Use Your Data">
          <P>We use your data to provide and improve the Honey Groove experience. This includes displaying your collection and activity to other users, matching you with records on your wantlist, generating your weekly Wax Report, calculating your collection value, and processing marketplace transactions. We use analytics data to understand how the platform is used and to improve features.</P>
        </Section>

        <Section title="What We Share">
          <P>We never sell your data. We do not share your data with third parties for advertising purposes. We share limited data with the following service providers who help us operate the platform:</P>
          <ul className="list-disc pl-6 text-sm text-vinyl-black/70 leading-relaxed mb-3 space-y-1">
            <li><strong>Stripe</strong> processes all marketplace payments. Stripe receives your payment information directly and is PCI-DSS compliant. We never store your card or bank details.</li>
            <li><strong>Discogs</strong> provides album art, record details, and market valuation data. We send search queries to Discogs on your behalf.</li>
            <li><strong>Resend</strong> delivers transactional emails such as verification emails, trade notifications, and weekly reports.</li>
            <li><strong>Google Analytics</strong> collects anonymized usage data to help us understand how the platform is used.</li>
          </ul>
        </Section>

        <Section title="How We Store and Protect Your Data">
          <P>Your data is stored in encrypted databases. Passwords are hashed using industry-standard bcrypt hashing. All data is transmitted over HTTPS. We follow security best practices to protect your information. Access to production data is restricted to the founding team only.</P>
        </Section>

        <Section title="Your Rights">
          <P>You can view and update your personal information from your profile settings at any time. You can request a full export of your data by contacting us. You can request account deletion from your profile settings. When you delete your account your profile, posts, and collection are removed. Transaction history is retained for dispute resolution purposes as described in our Terms of Service.</P>
        </Section>

        <Section title="Cookies">
          <P>We use essential cookies to keep you logged in and to remember your preferences. We use Google Analytics which sets its own cookies to track anonymized usage patterns. We do not use advertising cookies or tracking pixels from ad networks.</P>
        </Section>

        <Section title="We Never Sell Your Data">
          <P>This deserves its own section because it matters. The Honey Groove will never sell your personal data, your collection data, your listening history, or any other information to advertisers, data brokers, or anyone else. Our business model is transaction fees on marketplace sales, not your data. Your collection, your wantlist, and your listening history are yours.</P>
        </Section>

        <Section title="Changes to This Policy">
          <P>We may update this privacy policy from time to time. If we make significant changes we will notify you via email or through the app. Your continued use of the Honey Groove after changes are posted constitutes acceptance of the updated policy.</P>
        </Section>

        <Section title="Contact">
          <P>If you have questions about this privacy policy or how we handle your data reach out to us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>.</P>
        </Section>

        <Footer />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <div className="mb-8" data-testid={`privacy-section-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <h2 className="font-heading text-xl text-honey-amber mb-3">{title}</h2>
    {children}
  </div>
);

const P = ({ children }) => (
  <p className="text-sm text-vinyl-black/70 leading-relaxed mb-3">{children}</p>
);

const Footer = () => (
  <div className="mt-12 pt-8 border-t border-honey/20 flex items-center justify-between">
    <Link to="/" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Back to Home</Link>
    <div className="flex gap-4">
      <Link to="/terms" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Terms of Service</Link>
      <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">FAQ</Link>
    </div>
  </div>
);

export default PrivacyPage;
