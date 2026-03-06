import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';

const TermsPage = () => {
  usePageTitle('Terms of Service');
  return (
    <div className="min-h-screen bg-honey-cream">
      <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="terms-page">
        <h1 className="font-heading text-4xl text-vinyl-black mb-2">Terms of Service</h1>
        <p className="text-muted-foreground mb-10">Last updated March 2026</p>

        <Section title="Acceptance of Terms">
          <P>By accessing or using the Honey Groove you agree to be bound by these Terms of Service. If you do not agree to these terms do not use the service. We may update these terms from time to time and your continued use of the platform constitutes acceptance of any changes.</P>
        </Section>

        <Section title="Description of Service">
          <P>The Honey Groove is a social platform for vinyl collectors. We provide tools to track your vinyl collection, share listening activity, discover records, and buy, sell, and trade records with other collectors through our peer-to-peer marketplace called The Honeypot. All marketplace transactions are processed through Stripe.</P>
        </Section>

        <Section title="User Responsibilities">
          <P>You are responsible for maintaining the security of your account credentials. You must provide accurate information when creating your account. You are responsible for all activity that occurs under your account. You must be at least 18 years old to use the Honey Groove. You agree not to share your account with others or create multiple accounts.</P>
        </Section>

        <Section title="Marketplace Rules">
          <P>All records listed for sale or trade must be accurately described including condition, pressing details, and any defects. You must include at least one photo of the actual record you are selling. Prices must be listed in USD. All payments must be processed through the Honey Groove via Stripe. Sellers must ship within 5 days of a completed sale or accepted trade. Tracking numbers are required for all shipments.</P>
          <P>Sellers must connect a Stripe account before listing items for sale. New sellers with fewer than 3 completed transactions cannot list items priced above $150. This restriction lifts automatically once you reach 3 completed transactions.</P>
        </Section>

        <Section title="Transaction Fees">
          <P>The Honey Groove charges a 6% transaction fee on completed sales. For trades that include a cash sweetener we charge 6% of the sweetener amount only. The Mutual Hold amount is not subject to fees and is fully reversed on successful completion of a trade. Fees are deducted from the seller payout automatically.</P>
        </Section>

        <Section title="Mutual Hold System">
          <P>All trades on the Honey Groove require a Mutual Hold. Both parties are charged a hold amount equal to the estimated value of the records being traded. This hold is fully reversed within 24 hours of both parties confirming receipt of their records. If either party fails to ship within 5 days the other party can cancel the trade and both holds are reversed.</P>
        </Section>

        <Section title="Prohibited Conduct">
          <P>You may not use the Honey Groove to sell counterfeit or bootleg records without clear disclosure. You may not misrepresent the condition of records. You may not harass, threaten, or abuse other users. You may not attempt to conduct transactions outside of the platform. You may not post content that is illegal, defamatory, or violates the rights of others. You may not use automated tools to scrape data or create fake accounts.</P>
        </Section>

        <Section title="Dispute Resolution">
          <P>If you receive a record that is significantly not as described you have 48 hours after delivery confirmation to file a dispute. Both parties' holds are frozen during the dispute review. Our team reviews every dispute and will make a determination within 48 hours. Resolutions may include full refund, partial refund, or hold forfeiture depending on the circumstances. Our dispute resolution decisions are final.</P>
        </Section>

        <Section title="Limitation of Liability">
          <P>The Honey Groove provides a platform for collectors to connect and transact. We are not responsible for the condition of records sold or traded between users. We are not responsible for shipping delays, damage during transit, or lost packages. Our liability is limited to the transaction fees collected. We strongly recommend shipping insurance for items over $75.</P>
        </Section>

        <Section title="Termination">
          <P>We reserve the right to suspend or terminate accounts that violate these terms, engage in fraudulent activity, or receive repeated disputes. You may request account deletion from your profile settings at any time. Active trades or sales must be completed or cancelled before deletion. Completed transaction history is retained for dispute resolution purposes.</P>
        </Section>

        <Section title="Contact">
          <P>If you have questions about these terms reach out to us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>.</P>
        </Section>

        <Footer />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <div className="mb-8" data-testid={`terms-section-${title.toLowerCase().replace(/\s+/g, '-')}`}>
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
      <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Privacy Policy</Link>
      <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">FAQ</Link>
    </div>
  </div>
);

export default TermsPage;
