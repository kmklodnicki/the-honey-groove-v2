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
        <p className="text-muted-foreground mb-10">Last Updated: March 2026</p>

        <Section title="1. Introduction">
          <P>The Honey Groove, LLC ("The Honey Groove," "we," "us," or "our") operates thehoneygroove.com and the associated mobile application (collectively, the "Platform"). This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our Platform or use our services. Please read this policy carefully. If you do not agree with the terms of this Privacy Policy, please do not access the Platform.</P>
          <P>We reserve the right to make changes to this Privacy Policy at any time and for any reason. We will alert you about any changes by updating the "Last Updated" date of this Privacy Policy. You are encouraged to periodically review this Privacy Policy to stay informed of updates.</P>
        </Section>

        <Section title="2. Information We Collect">
          <SubSection title="2.1 Information You Provide Directly">
            <P>We collect information that you voluntarily provide to us when you register on the Platform, create a profile, use our features, participate in marketplace transactions, or contact us. This includes:</P>
            <UL items={[
              'Account information: username, email address, password (stored in hashed form)',
              'Profile information: display name, profile photo, bio, and any other information you add to your profile',
              'Collection data: records you add to your Vault, condition grades, personal notes, and Dream List entries',
              'User-uploaded content: photographs of album covers, posts in the Hive, comments, and haul submissions',
              'Marketplace data: listing descriptions, pricing, shipping information, and transaction communications',
              'Payment information: when you connect a Stripe account for selling, or when you purchase items or platform features (payment details are processed and stored by Stripe, not by us)',
              'Communications: messages sent through the Platform, dispute submissions, and correspondence with our support team',
              'Import data: when you import your collection from a third-party service, we temporarily access your collection through OAuth to extract release identifiers. We do not store your username, password, or OAuth token after the import is complete.',
            ]} />
          </SubSection>

          <SubSection title="2.2 Information Collected Automatically">
            <P>When you access the Platform, we may automatically collect certain information about your device and usage, including:</P>
            <UL items={[
              'Device information: device type, operating system, browser type, screen resolution, and unique device identifiers',
              'Log data: IP address, access times, pages viewed, referring URL, and actions taken on the Platform',
              'Usage data: features used, frequency of use, search queries, and interaction patterns',
              'Location data: approximate geographic location based on your IP address (we do not collect precise GPS location)',
              'Cookies and similar technologies: we use cookies, local storage, and similar technologies to maintain your session, remember preferences, and analyze usage patterns. See Section 7 for details.',
            ]} />
          </SubSection>

          <SubSection title="2.3 Information from Third Parties">
            <P>We may receive information about you from third-party services that you connect to the Platform:</P>
            <UL items={[
              'Collection import services: when you authorize an import, we receive a list of release identifiers from your collection. We extract only release IDs and discard all other user data immediately after import.',
              'Spotify: we use the Spotify API to retrieve album metadata and artwork. We do not access your personal Spotify account, listening history, or playlists.',
              'Stripe: we receive limited transaction information from Stripe related to your marketplace activity, including transaction status and payout details. We do not receive or store your full credit card number.',
            ]} />
          </SubSection>
        </Section>

        <Section title="3. How We Use Your Information">
          <P>We use the information we collect for the following purposes:</P>
          <UL items={[
            'To create and maintain your account and provide the core functionality of the Platform',
            'To process marketplace transactions, including sales, trades, payments, refunds, and dispute resolution',
            'To display your collection, posts, and marketplace listings to other users as part of the social and marketplace features',
            'To match your collection records with album artwork from third-party music APIs',
            'To calculate collection valuations and pricing estimates using market data',
            'To send you transactional communications (order confirmations, shipping updates, dispute notifications)',
            'To send you service-related announcements (feature updates, policy changes, maintenance notices)',
            'To improve, personalize, and optimize the Platform and user experience',
            'To detect, prevent, and address fraud, abuse, security issues, and technical problems',
            'To enforce our Terms of Service and Community Guidelines',
            'To comply with legal obligations and respond to lawful requests from public authorities',
          ]} />
        </Section>

        <Section title="4. How We Share Your Information">
          <P>We do not sell your personal information. We may share your information in the following limited circumstances:</P>

          <SubSection title="4.1 With Other Users">
            <P>Certain information is visible to other users as part of the Platform's social and marketplace features. This includes your username, profile photo, public collection data, Hive posts, marketplace listings, and transaction ratings. You can control some of this visibility through your privacy settings.</P>
          </SubSection>

          <SubSection title="4.2 With Service Providers">
            <P>We share information with third-party service providers who perform services on our behalf:</P>
            <UL items={[
              'Stripe, Inc.: processes payments, manages seller payouts, and handles Mutual Hold transactions. Stripe\'s privacy policy governs their handling of your payment data.',
              'Cloudinary: hosts user-uploaded images (profile photos, album cover photos, haul images). Images are stored on Cloudinary\'s servers.',
              'MongoDB Atlas: our database provider. User data is stored on MongoDB Atlas infrastructure.',
              'Vercel: our hosting provider. The Platform is deployed on Vercel\'s infrastructure.',
              'Analytics providers: we may use analytics services to understand Platform usage. These services may collect anonymized usage data.',
            ]} />
          </SubSection>

          <SubSection title="4.3 For Legal Reasons">
            <P>We may disclose your information if required to do so by law or in response to valid legal process, including subpoenas, court orders, or government requests. We may also disclose information when we believe in good faith that disclosure is necessary to protect our rights, protect your safety or the safety of others, investigate fraud, or respond to a government request.</P>
          </SubSection>

          <SubSection title="4.4 Business Transfers">
            <P>If The Honey Groove is involved in a merger, acquisition, reorganization, or sale of assets, your information may be transferred as part of that transaction. We will notify you via email or a prominent notice on the Platform of any change in ownership or use of your personal information.</P>
          </SubSection>
        </Section>

        <Section title="5. Data Retention">
          <P>We retain your personal information for as long as your account is active or as needed to provide you with the Service. Specific retention periods:</P>
          <UL items={[
            'Account data: retained until you request account deletion',
            'Collection and Vault data: retained until you request account deletion',
            'Hive posts and comments: retained until you delete them or request account deletion',
            'Marketplace transaction history: retained for 3 years after transaction completion for dispute resolution and legal compliance',
            'Payment records: retained as required by applicable tax and financial reporting laws',
            'User-uploaded images: retained in Cloudinary until you delete them or request account deletion. Community-contributed cover art may be retained per the license granted in our Terms of Service.',
            'Third-party OAuth tokens: discarded immediately after import completion (not retained)',
            'Analytics and log data: retained for up to 12 months, then anonymized or deleted',
          ]} />
        </Section>

        <Section title="6. Your Rights and Choices">
          <SubSection title="6.1 Account Information">
            <P>You may update, correct, or delete your account information at any time through your profile settings. You may request deletion of your account by contacting <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> or through the account settings page. Upon deletion, we will remove your personal data, subject to any legal retention requirements.</P>
          </SubSection>

          <SubSection title="6.2 California Residents (CCPA)">
            <P>If you are a California resident, you have additional rights under the California Consumer Privacy Act (CCPA):</P>
            <UL items={[
              'Right to know: You may request information about the categories and specific pieces of personal information we have collected about you.',
              'Right to delete: You may request that we delete your personal information, subject to certain exceptions.',
              'Right to opt-out of sale: We do not sell personal information. No opt-out is necessary.',
              'Right to non-discrimination: We will not discriminate against you for exercising your CCPA rights.',
            ]} />
            <P>To exercise your CCPA rights, contact us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>. We will verify your identity before fulfilling any request.</P>
          </SubSection>

          <SubSection title="6.3 Email Communications">
            <P>You may opt out of non-essential email communications (such as feature announcements or promotional messages) by clicking the unsubscribe link in any email or by updating your notification preferences in your account settings. You cannot opt out of transactional emails related to your account, marketplace activity, or legal notices.</P>
          </SubSection>
        </Section>

        <Section title="7. Cookies and Tracking Technologies">
          <P>We use cookies and similar technologies to operate the Platform. The types of cookies we use include:</P>
          <UL items={[
            'Essential cookies: required for the Platform to function (authentication, session management, security). These cannot be disabled.',
            'Functional cookies: remember your preferences and settings (theme, language, display options).',
            'Analytics cookies: help us understand how users interact with the Platform so we can improve it. These may be provided by third-party analytics services.',
          ]} />
          <P>We do not use advertising cookies or third-party tracking cookies for targeted advertising. Most web browsers allow you to control cookies through your browser settings. Disabling essential cookies may prevent you from using certain features of the Platform.</P>
        </Section>

        <Section title="8. Data Security">
          <P>We implement reasonable administrative, technical, and physical security measures to protect your personal information from unauthorized access, use, or disclosure. These measures include encrypted data transmission (HTTPS/TLS), hashed password storage, access controls, and regular security reviews. However, no method of transmission over the Internet or electronic storage is 100% secure. We cannot guarantee absolute security of your data.</P>
        </Section>

        <Section title="9. Children's Privacy">
          <P>The Platform is not intended for individuals under the age of 18. We do not knowingly collect personal information from children under 18. If we learn that we have collected personal information from a child under 18, we will take steps to delete that information as quickly as possible. If you believe we have collected information from a child under 18, please contact us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>.</P>
        </Section>

        <Section title="10. International Users">
          <P>The Platform is operated from the United States. If you access the Platform from outside the United States, please be aware that your information may be transferred to, stored, and processed in the United States, where data protection laws may differ from those of your country. By using the Platform, you consent to the transfer of your information to the United States.</P>
        </Section>

        <Section title="11. Third-Party Links">
          <P>The Platform may contain links to third-party websites and services, including music data providers, payment processors, and other platforms. We are not responsible for the privacy practices of these third-party sites. We encourage you to review the privacy policies of any third-party services you access through the Platform.</P>
        </Section>

        <Section title="12. Changes to This Privacy Policy">
          <P>We may update this Privacy Policy from time to time. If we make material changes, we will notify you by email or through a prominent notice on the Platform prior to the change becoming effective. Your continued use of the Platform after the effective date of the revised Privacy Policy constitutes your acceptance of the changes.</P>
        </Section>

        <Section title="13. Contact Us">
          <P>If you have questions or concerns about this Privacy Policy, or if you wish to exercise any of your rights described herein, please contact us:</P>
          <P>Email: <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a><br />Website: <a href="https://thehoneygroove.com" className="text-honey-amber hover:underline">thehoneygroove.com</a></P>
        </Section>

        <p className="text-xs text-vinyl-black/30 text-center mt-8">End of Privacy Policy</p>

        <Footer />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <div className="mb-8" data-testid={`privacy-section-${title.toLowerCase().replace(/[\s.]+/g, '-')}`}>
    <h2 className="font-heading text-xl text-honey-amber mb-3">{title}</h2>
    {children}
  </div>
);

const SubSection = ({ title, children }) => (
  <div className="mb-4">
    <h3 className="font-semibold text-sm text-vinyl-black mb-2">{title}</h3>
    {children}
  </div>
);

const P = ({ children }) => (
  <p className="text-sm text-vinyl-black/70 leading-relaxed mb-3">{children}</p>
);

const UL = ({ items }) => (
  <ul className="list-disc pl-5 mb-3 space-y-1">
    {items.map((item, i) => (
      <li key={i} className="text-sm text-vinyl-black/70 leading-relaxed">{item}</li>
    ))}
  </ul>
);

const Footer = () => (
  <div className="mt-12 pt-8 border-t border-honey/20 flex items-center justify-between">
    <Link to="/" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Back to Home</Link>
    <div className="flex gap-4">
      <Link to="/terms" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Terms of Service</Link>
      <Link to="/guidelines" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Guidelines</Link>
      <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">FAQ</Link>
    </div>
  </div>
);

export default PrivacyPage;
