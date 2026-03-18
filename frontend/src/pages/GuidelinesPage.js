import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import SEOHead from '../components/SEOHead';

const GuidelinesPage = () => {
  usePageTitle('Community Guidelines');
  return (
    <div className="min-h-screen bg-honey-cream">
      <SEOHead
        title="Community Guidelines"
        description="Community Guidelines for The Honey Groove vinyl collecting community."
        url="/guidelines"
      />
      <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="guidelines-page">
        <h1 className="font-heading text-4xl text-vinyl-black mb-2">Community Guidelines</h1>
        <p className="text-muted-foreground mb-10">Last Updated: March 2026</p>

        <Section title="1. Our Community">
          <P>The Honey Groove is a community of vinyl collectors, music lovers, and enthusiasts who share a passion for physical music. These Community Guidelines exist to keep the Hive a positive, respectful, and trustworthy space for everyone. These guidelines apply to all areas of the Platform, including the Hive (social feed), the Honeypot (marketplace), messaging, comments, profile content, and any other user interactions.</P>
          <P>By using The Honey Groove, you agree to follow these guidelines. Violations may result in content removal, temporary suspension, or permanent account termination at our discretion. These guidelines are incorporated by reference into our Terms of Service.</P>
        </Section>

        <Section title="2. Be Respectful">
          <P>The Honey Groove is built on mutual respect between collectors. We expect all users to treat each other with courtesy and good faith.</P>

          <SubSection title="2.1 No Harassment or Bullying">
            <P>Do not engage in behavior that targets, intimidates, or demeans other users. This includes:</P>
            <UL items={[
              'Personal attacks, name-calling, or insults directed at other users',
              'Repeated unwanted contact or messaging after being asked to stop',
              'Targeting someone based on their race, ethnicity, gender, sexual orientation, religion, disability, or any other protected characteristic',
              'Doxxing (sharing someone\'s personal information without their consent)',
              'Coordinated harassment or encouraging others to target a specific user',
              'Threatening physical harm or violence against any person',
            ]} />
          </SubSection>

          <SubSection title="2.2 No Hate Speech">
            <P>Content that promotes hatred, violence, or discrimination against individuals or groups based on race, ethnicity, nationality, gender, gender identity, sexual orientation, religion, disability, age, or any other protected characteristic is not permitted. This includes slurs, dehumanizing language, symbols of hate groups, and content that glorifies or trivializes atrocities or acts of mass violence.</P>
          </SubSection>

          <SubSection title="2.3 Constructive Disagreements">
            <P>Disagreements about music, collecting, grading, and pricing are natural and welcome. Debate the ideas, not the person. Critique a record's grading, not the seller's character. If a conversation becomes heated, step away or use the block function.</P>
          </SubSection>
        </Section>

        <Section title="3. Content Standards">
          <SubSection title="3.1 Keep It About the Music">
            <P>The Honey Groove is a vinyl collecting community. Posts, comments, and content should relate to music, vinyl records, collecting, audio equipment, record stores, listening experiences, or the broader music culture. Off-topic content that doesn't connect back to the community's purpose may be removed.</P>
          </SubSection>

          <SubSection title="3.2 Photos and Visual Content">
            <P>The Hive is a visual space. We encourage high-quality photos of your records, setups, hauls, and listening sessions. The following rules apply to all visual content:</P>
            <UL items={[
              'Photos should be yours or taken with permission. Do not post others\' photos without credit.',
              'Album cover art uploaded to the Platform should be clean photographs of physical releases you own.',
              'Nudity and graphic content: extremely nude photos or extremely graphic images will be automatically blurred and flagged for review. Artistic album covers that contain nudity (as they appear on the physical release) are permitted when shared in the context of discussing or showcasing the record. However, user-generated photos containing nudity, sexual content, or graphic violence that are not album artwork are not permitted.',
              'Do not post content depicting illegal activity, self-harm, or content that exploits minors.',
            ]} />
          </SubSection>

          <SubSection title="3.3 Spam and Self-Promotion">
            <P>Do not use The Honey Groove primarily as an advertising platform. Reasonable self-promotion is allowed within context:</P>
            <UL items={[
              'Sharing your own Honeypot listings in the Hive is fine',
              'Sharing your own music-related content (blog posts, YouTube videos, playlists) occasionally is fine',
              'Repetitive posting of the same content or links is not allowed',
              'Automated posting, bot activity, or mass messaging is not allowed',
              'Promoting competing marketplace platforms is not allowed',
            ]} />
          </SubSection>

          <SubSection title="3.4 Misinformation">
            <P>Do not deliberately spread false information about records, pressings, or other users. This includes fabricating pressing details, making false claims about a record's authenticity, or creating fake transaction reviews.</P>
          </SubSection>
        </Section>

        <Section title="4. Marketplace Conduct">
          <SubSection title="4.1 Honest Listings">
            <P>Marketplace integrity is essential. All listings must be truthful and complete:</P>
            <UL items={[
              'Accurately describe the condition of every record using standard grading terminology',
              'Disclose all defects, damage, seam splits, ring wear, and playback issues',
              'Include photos of the actual item you are selling (not stock photos or images from other sources)',
              'If a record is a bootleg, unofficial pressing, or counterfeit, you must clearly disclose this in the listing title and description',
              'Do not misrepresent a reissue as an original pressing',
            ]} />
          </SubSection>

          <SubSection title="4.2 Pricing">
            <P>You are free to price your records however you choose. However:</P>
            <UL items={[
              'Price gouging during limited-release hype periods is discouraged (but not prohibited)',
              'Shill listings (fake listings to manipulate market pricing) are prohibited and will result in account termination',
              'Completing sham transactions to inflate your seller rating or bypass new seller restrictions is prohibited',
            ]} />
          </SubSection>

          <SubSection title="4.3 Communication">
            <P>When communicating with buyers, sellers, or trade partners:</P>
            <UL items={[
              'Respond to messages in a timely manner (within 24 hours is a good standard)',
              'Be honest about shipping timelines and any delays',
              'Do not attempt to move transactions off-platform',
              'Do not use marketplace messaging to harass, threaten, or pressure other users',
            ]} />
          </SubSection>

          <SubSection title="4.4 Shipping">
            <P>Proper shipping protects both parties:</P>
            <UL items={[
              'Ship within 3 business days of a completed sale or accepted trade',
              'Provide tracking information for every shipment',
              'Pack records appropriately (mailers designed for vinyl, cardboard stiffeners, etc.)',
              'Shipping insurance is strongly recommended for items over $75',
            ]} />
          </SubSection>
        </Section>

        <Section title="5. Account Integrity">
          <UL items={[
            'One account per person. Do not create multiple accounts for any reason.',
            'Do not impersonate other users, public figures, or brands.',
            'Do not use misleading usernames or profile information to deceive others.',
            'Do not share your account credentials with anyone.',
            'Do not buy, sell, or trade accounts.',
          ]} />
        </Section>

        <Section title="6. Intellectual Property">
          <P>Respect the intellectual property of others:</P>
          <UL items={[
            'Do not post copyrighted music, full album streams, or pirated content',
            'Do not post photos or content stolen from other users or websites without proper attribution',
            'Album cover photos you upload should be your own photographs of a physical product you own',
            'Sharing short clips for commentary or review purposes is generally acceptable under fair use, but do not post full tracks or albums',
          ]} />
        </Section>

        <Section title="7. Reporting and Enforcement">
          <SubSection title="7.1 How to Report">
            <P>If you encounter content or behavior that violates these guidelines, please report it using the report button available on all posts, comments, listings, and user profiles. You can also contact us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> with details of the violation. All reports are reviewed by our team.</P>
          </SubSection>

          <SubSection title="7.2 Enforcement Actions">
            <P>We take a graduated approach to enforcement, but reserve the right to skip steps for severe violations:</P>
            <UL items={[
              'Warning: a notification that your content or behavior has violated the guidelines, with a request to stop.',
              'Content removal: the offending content is removed from the Platform.',
              'Temporary suspension: your account is suspended for a defined period (24 hours to 30 days depending on severity).',
              'Permanent ban: your account is permanently terminated. This is reserved for severe or repeated violations, fraud, or illegal activity.',
            ]} />
            <P>Actions that result in immediate permanent ban include:</P>
            <UL items={[
              'Threats of physical violence',
              'Doxxing or sharing personal information of other users',
              'Posting content that exploits minors',
              'Confirmed fraud or scam activity',
              'Repeated harassment after warnings',
            ]} />
          </SubSection>

          <SubSection title="7.3 Appeals">
            <P>If you believe an enforcement action was taken in error, you may appeal by emailing <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> within 14 days of the action. Include your username, a description of the action taken, and your reasoning for the appeal. Our team will review appeals within 7 business days. Appeal decisions are final.</P>
          </SubSection>
        </Section>

        <Section title="8. Changes to These Guidelines">
          <P>We may update these Community Guidelines from time to time to reflect changes in our community, Platform features, or applicable laws. Material changes will be communicated through the Platform or via email. Your continued use of The Honey Groove after changes are posted constitutes acceptance of the updated guidelines.</P>
        </Section>

        <Section title="9. Contact">
          <P>If you have questions about these Community Guidelines, please contact us:</P>
          <P>Email: <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a><br />Website: <a href="https://thehoneygroove.com" className="text-honey-amber hover:underline">thehoneygroove.com</a></P>
        </Section>

        <p className="text-xs text-vinyl-black/30 text-center mt-8">End of Community Guidelines</p>

        <Footer />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <div className="mb-8" data-testid={`guidelines-section-${title.toLowerCase().replace(/[\s.]+/g, '-')}`}>
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
      <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Privacy Policy</Link>
    </div>
  </div>
);

export default GuidelinesPage;
