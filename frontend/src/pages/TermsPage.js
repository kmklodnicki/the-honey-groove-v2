import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import SEOHead from '../components/SEOHead';

const TermsPage = () => {
  usePageTitle('Terms of Service');
  return (
    <div className="min-h-screen bg-honey-cream">
      <SEOHead
        title="Terms of Service"
        description="Terms of Service for The Honey Groove vinyl social platform and marketplace."
        url="/terms"
      />
      <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="terms-page">
        <h1 className="font-heading text-4xl text-vinyl-black mb-2">Terms of Service</h1>
        <p className="text-muted-foreground mb-10">Last Updated: March 2026</p>

        <Section title="1. Acceptance of Terms">
          <P>By accessing, browsing, or using The Honey Groove (the "Platform"), including any associated websites, mobile applications, APIs, or services (collectively, the "Service"), you ("User," "you," or "your") acknowledge that you have read, understood, and agree to be bound by these Terms of Service ("Terms" or "Agreement"). If you do not agree to these Terms in their entirety, you must immediately cease all use of the Service.</P>
          <P>These Terms constitute a legally binding agreement between you and The Honey Groove, LLC ("The Honey Groove," "we," "us," or "our"). We reserve the right to modify, amend, or update these Terms at any time in our sole discretion. Material changes will be communicated via email to the address associated with your account or through a prominent notice on the Platform. Your continued use of the Service after such modifications constitutes your acceptance of the updated Terms. If you do not agree to any modification, your sole remedy is to discontinue use of the Service.</P>
          <P>These Terms incorporate by reference our Privacy Policy, Community Guidelines, and any other policies posted on the Platform, all of which form part of this Agreement.</P>
        </Section>

        <Section title="2. Eligibility">
          <P>You must be at least 18 years of age to use the Service. By creating an account, you represent and warrant that you are at least 18 years old, that you have the legal capacity to enter into this Agreement, and that your use of the Service complies with all applicable local, state, national, and international laws and regulations.</P>
          <P>If you are using the Service on behalf of a business, organization, or other entity, you represent and warrant that you have the authority to bind that entity to these Terms, and "you" and "your" will refer to both you individually and that entity.</P>
          <P>We reserve the right to request verification of your age or identity at any time and to suspend or terminate accounts that we reasonably believe are operated by individuals under 18 years of age.</P>
        </Section>

        <Section title="3. Description of Service">
          <P>The Honey Groove is a social platform for vinyl record collectors. The Service provides tools to catalog and manage your vinyl collection (the "Vault"), share listening activity and engage with other collectors through a social feed (the "Hive"), discover records, and buy, sell, and trade vinyl records with other users through our peer-to-peer marketplace (the "Honeypot"). All marketplace payment processing is handled through Stripe, Inc. ("Stripe").</P>
          <P>The Service is provided on an "as is" and "as available" basis. We reserve the right to modify, suspend, or discontinue any aspect of the Service at any time, with or without notice, and without liability to you or any third party. We do not guarantee that the Service will be uninterrupted, timely, secure, or error-free.</P>
          <P>Third-Party Data: Portions of the catalog data displayed on the Platform are sourced from third-party APIs, including the Discogs API and the Spotify API. This application uses the Discogs API but is not affiliated with, sponsored, or endorsed by Discogs. "Discogs" is a trademark of Zink Media, LLC. Album artwork displayed on the Platform may be provided by Spotify. We do not guarantee the accuracy, completeness, or availability of any third-party data.</P>

          <SubSection title="3.1 Paid Features and Subscriptions">
            <P>The Honey Groove offers optional paid features and subscription plans that provide enhanced functionality. These include, but are not limited to:</P>
            <UL items={[
              'THG Gold: a premium subscription plan available at a monthly or annual rate. Gold subscribers receive benefits such as reduced marketplace transaction fees (4% instead of 6%), advanced collection analytics, price alerts, enhanced search filters, free streak restores, and other premium features as described on the Platform.',
              'Streak restores: a one-time purchase that allows you to recover a daily prompt streak that has been broken.',
              'Promoted listings: optional paid promotion for marketplace listings to increase visibility.',
            ]} />
            <P>Subscription fees are billed in advance on a recurring basis (monthly or annually, depending on the plan selected) through Stripe. You may cancel your subscription at any time through your account settings. Cancellation takes effect at the end of the current billing period. No partial refunds are issued for unused portions of a billing period. We reserve the right to modify subscription pricing and features with 30 days' notice to active subscribers.</P>
          </SubSection>
        </Section>

        <Section title="4. User Accounts">
          <SubSection title="4.1 Account Creation and Security">
            <P>To access certain features of the Service, you must create an account. You agree to provide accurate, current, and complete information during registration and to update such information as necessary. You are solely responsible for maintaining the confidentiality of your account credentials, including your password. You are solely responsible for all activities that occur under your account, whether or not you have authorized such activities.</P>
            <P>You agree to immediately notify us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> if you become aware of any unauthorized use of your account or any other breach of security. We will not be liable for any loss or damage arising from your failure to protect your account credentials.</P>
          </SubSection>
          <SubSection title="4.2 Account Restrictions">
            <P>You may not create or maintain more than one account. You may not share your account credentials with any other person. You may not transfer, sell, or assign your account to any other person. We reserve the right to merge, suspend, or terminate duplicate accounts at our discretion.</P>
          </SubSection>
        </Section>

        <Section title="5. User Content">
          <SubSection title="5.1 Content Ownership">
            <P>You retain ownership of any content you submit, post, or upload to the Service, including but not limited to photographs, text, comments, reviews, and marketplace listings (collectively, "User Content"). By submitting User Content to the Platform, you grant The Honey Groove a worldwide, non-exclusive, royalty-free, sublicensable, transferable license to use, reproduce, distribute, prepare derivative works of, display, and perform your User Content in connection with the Service, including for the purpose of promoting and redistributing part or all of the Service in any media formats and through any media channels now known or hereafter developed.</P>
            <P>This license includes the right to make User Content available to other users of the Service and to use User Content for the operation, improvement, and promotion of the Platform. This license persists for as long as the User Content remains on the Platform and for a reasonable period thereafter to accommodate cached or archived copies, backup systems, and operational needs.</P>
          </SubSection>
          <SubSection title="5.2 Community-Contributed Album Art">
            <P>When you upload a photograph of an album cover to the Platform, you grant The Honey Groove an additional perpetual, irrevocable, worldwide, royalty-free license to use, display, reproduce, and distribute that image as album artwork across the Platform for all users who have the same release in their collection. You represent and warrant that any album cover photograph you upload was taken by you, that it depicts a physical product you own, and that your upload does not infringe on any third-party intellectual property rights.</P>
            <P>Community-contributed album art may be displayed to other users of the Platform, used in promotional materials, and retained even if you delete your account or remove the associated record from your collection. You may not upload images that you do not have the right to share, including images downloaded from other websites, copyrighted promotional materials, or images belonging to other users.</P>
          </SubSection>
          <SubSection title="5.3 Content Restrictions">
            <P>You are solely responsible for your User Content and the consequences of posting it. You represent and warrant that your User Content does not and will not:</P>
            <UL items={[
              'Infringe, misappropriate, or violate any third-party intellectual property, privacy, publicity, or other rights',
              'Contain material that is defamatory, obscene, threatening, harassing, abusive, hateful, or otherwise objectionable',
              'Contain false, misleading, or deceptive statements or representations',
              'Contain viruses, malware, or any other harmful code or technology',
              'Promote illegal activities or violate any applicable law or regulation',
              'Impersonate any person or entity or misrepresent your affiliation with any person or entity',
              'Contain unsolicited advertising, spam, or promotional material',
            ]} />
          </SubSection>
          <SubSection title="5.4 Content Moderation">
            <P>We reserve the right, but have no obligation, to monitor, review, edit, or remove any User Content at our sole discretion and without notice. We may remove content that we determine, in our sole judgment, violates these Terms, our Community Guidelines, or applicable law. We are not responsible for any User Content posted by users of the Service.</P>
          </SubSection>
        </Section>

        <Section title="6. The Honeypot Marketplace">
          <SubSection title="6.1 General Terms">
            <P>The Honeypot is a peer-to-peer marketplace that facilitates transactions between individual users. The Honey Groove is not a party to any transaction between buyers and sellers. We do not take possession of, inspect, authenticate, or guarantee any records listed on the Marketplace. We are a platform, not a seller, buyer, broker, agent, or intermediary. All transactions are conducted directly between users, with payment processing facilitated by Stripe.</P>
          </SubSection>
          <SubSection title="6.2 Listing Requirements">
            <P>All records listed for sale or trade must be accurately described, including condition grading (using the Goldmine standard or equivalent), pressing details, and disclosure of any defects, damage, or notable characteristics. Sellers must include at least one photograph of the actual physical record being sold or traded (stock photos, images from other websites, or AI-generated images are prohibited). Prices must be listed in United States Dollars (USD). All sales payments must be processed through the Platform via Stripe. Attempting to redirect transactions off-platform is a violation of these Terms and grounds for immediate account termination.</P>
          </SubSection>
          <SubSection title="6.3 Seller Obligations">
            <P>By listing an item for sale or trade, you represent and warrant that you are the lawful owner of the item, that you have the right to sell or trade it, that the item is accurately described in your listing, and that the item is not counterfeit (unless clearly disclosed as a bootleg or unofficial pressing). Sellers must connect a valid Stripe account before listing items. Sellers must ship items within 3 business days of a completed sale or accepted trade. Tracking numbers are required for all shipments and must be entered on the Platform.</P>
          </SubSection>
          <SubSection title="6.4 New Seller Restrictions">
            <P>New sellers with fewer than 3 completed transactions may not list items priced above $150 USD. This restriction is lifted automatically upon completion of 3 transactions. This policy exists to protect buyers and maintain marketplace integrity. Attempts to circumvent this restriction (such as completing sham transactions) will result in account termination.</P>
          </SubSection>
          <SubSection title="6.5 Transaction Fees">
            <P>The Honey Groove charges a transaction fee of 6% on all completed sales, deducted automatically from the seller's payout. For trades that include a cash sweetener, the 6% fee applies only to the sweetener amount. Pure trades (no sweetener) are free and incur no platform fee. THG Gold subscribers receive a reduced fee of 4% on both sales and sweetener amounts. The Mutual Hold amount (described in Section 6.6) is a protective mechanism and is not subject to fees. All fees are non-refundable except where required by applicable law. We reserve the right to modify our fee structure at any time with 30 days' notice to active sellers.</P>
          </SubSection>
          <SubSection title="6.6 Mutual Hold System">
            <P>All trades conducted through the Honeypot require a Mutual Hold. Both parties are charged a hold amount equal to the estimated market value of the records being traded, plus a 15% protection buffer. Hold values are determined using The Honey Groove's pricing data, third-party market data, or, when no market data is available, a value agreed upon by both parties. This hold is an authorization only and is not a charge to your card. The hold is fully released within 48 hours of both parties confirming receipt of their records in the condition described.</P>
            <P>If either party fails to ship within 3 business days, the other party may cancel the trade, and both holds are released. Auth-holds may be periodically refreshed to maintain validity during the trade window. By initiating or accepting a trade, you authorize The Honey Groove to place, refresh, and, where warranted by a dispute ruling, capture holds on your payment method in accordance with these Terms. If a dispute is resolved against you, your hold may be captured and the funds transferred to the other party as indemnification for their loss. The amount captured will not exceed the original hold amount placed on your card.</P>
          </SubSection>
          <SubSection title="6.7 Buyer Obligations">
            <P>Buyers agree to pay the listed price plus any applicable shipping fees through the Platform. Buyers must inspect received items promptly and confirm receipt on the Platform within 48 hours of delivery. Failure to confirm receipt within 48 hours constitutes constructive acceptance of the item as described. Buyers may not initiate chargebacks or payment reversals through their bank or credit card provider for disputes that should be resolved through the Platform's dispute resolution process (Section 7). Initiating a chargeback outside of the Platform's dispute process is a violation of these Terms and grounds for account suspension or termination.</P>
          </SubSection>
          <SubSection title="6.8 Prohibited Listings">
            <P>The following items may not be listed on the Honeypot:</P>
            <UL items={[
              'Counterfeit or bootleg records without clear disclosure as such in the listing title and description',
              'Items you do not currently possess or have the legal right to sell',
              'Non-vinyl items (CDs, cassettes, digital media, or non-music merchandise are not permitted unless bundled with a vinyl listing)',
              'Stolen property',
              'Any item whose sale would violate applicable law',
            ]} />
          </SubSection>
        </Section>

        <Section title="7. Dispute Resolution Between Users">
          <SubSection title="7.1 Filing a Dispute">
            <P>If you receive a record that is significantly not as described in the listing, you have 48 hours after delivery confirmation to file a dispute through the Platform. Disputes must include a description of the issue and photographic evidence. Failure to file a dispute within the 48-hour window constitutes acceptance of the item as received.</P>
          </SubSection>
          <SubSection title="7.2 Dispute Review Process">
            <P>Upon receipt of a dispute, both parties' Mutual Holds (for trades) or the seller's payout (for sales) are frozen pending resolution. Our team reviews every dispute and will issue a determination within 48 hours of receiving all necessary information from both parties. Both parties will be given an opportunity to respond to the dispute with additional information or evidence.</P>
          </SubSection>
          <SubSection title="7.3 Dispute Outcomes">
            <P>Resolutions may include, at our sole discretion:</P>
            <UL items={[
              'Full refund to the buyer and return of the item to the seller at the seller\'s expense',
              'Partial refund reflecting the difference between the described and actual condition',
              'Hold capture and transfer to the other party if the dispute is resolved against you. Captured funds cover the estimated market value of the other party\'s lost item. The amount captured will not exceed the original hold amount placed on your card.',
              'Both holds released with no capture if the issue is determined to be caused by shipping damage (neither party at fault)',
              'No action if the dispute is found to be without merit',
              'Account suspension or termination for either party based on the findings, including for filing a dispute determined to be fraudulent',
            ]} />
          </SubSection>
          <SubSection title="7.4 Finality of Decisions">
            <P>The Honey Groove's dispute resolution decisions are final and binding on both parties. By using the Marketplace, you agree to accept our dispute determinations as the exclusive remedy for transaction disputes between users. This dispute resolution process does not limit any rights you may have under applicable consumer protection laws.</P>
          </SubSection>
        </Section>

        <Section title="8. Prohibited Conduct">
          <P>You agree not to engage in any of the following activities while using the Service:</P>
          <UL items={[
            'Harass, threaten, intimidate, stalk, or abuse any other user',
            'Post or transmit any content that is illegal, defamatory, fraudulent, or infringes on the rights of others',
            'Misrepresent your identity, affiliation, or the condition of items listed for sale or trade',
            'Attempt to conduct transactions outside of the Platform to avoid fees or protections',
            'Use automated tools, bots, scrapers, or scripts to access, collect, or interact with the Service or its data without our express written permission',
            'Create fake accounts, shill reviews, or engage in any form of platform manipulation',
            'Reverse engineer, decompile, disassemble, or otherwise attempt to derive the source code of the Service',
            'Interfere with or disrupt the Service, servers, or networks connected to the Service',
            'Collect or store personal information about other users without their express consent',
            'Use the Service for any commercial purpose not expressly permitted by these Terms',
            'Circumvent any security, authentication, or access control mechanisms of the Service',
            'Use the Service to distribute malware, viruses, or other harmful technology',
            'Engage in price manipulation, shill bidding, or any scheme to artificially inflate or deflate record values',
            'Violate any applicable local, state, national, or international law or regulation',
          ]} />
        </Section>

        <Section title="9. Intellectual Property">
          <SubSection title="9.1 Platform Ownership">
            <P>The Service, including its original content, features, functionality, design, graphics, logos, trademarks, and all associated intellectual property (collectively, "Platform IP"), is and will remain the exclusive property of The Honey Groove and its licensors. The Platform IP is protected by copyright, trademark, patent, trade secret, and other intellectual property laws. Nothing in these Terms grants you any right, title, or interest in the Platform IP except for the limited license to use the Service as set forth herein.</P>
            <P>"The Honey Groove," "The Honeypot," "The Hive," "The Vault," "Wax Report," "Beekeeper," and the associated logos and visual identity are trademarks of The Honey Groove, LLC. You may not use these marks without our prior written permission.</P>
          </SubSection>
          <SubSection title="9.2 Limited License">
            <P>Subject to your compliance with these Terms, we grant you a limited, non-exclusive, non-transferable, non-sublicensable, revocable license to access and use the Service for your personal, non-commercial purposes (except for authorized Marketplace transactions). This license does not include the right to modify, reproduce, distribute, create derivative works of, publicly display, publicly perform, republish, download, store, or transmit any Platform IP, except as incidentally necessary to use the Service as intended.</P>
          </SubSection>
          <SubSection title="9.3 DMCA and Copyright Complaints">
            <P>We respect the intellectual property rights of others. If you believe that any User Content posted on the Platform infringes your copyright, you may submit a notice pursuant to the Digital Millennium Copyright Act ("DMCA") by sending the following information to <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>:</P>
            <UL items={[
              'A physical or electronic signature of the copyright owner or authorized agent',
              'Identification of the copyrighted work claimed to have been infringed',
              'Identification of the material that is claimed to be infringing, with sufficient detail for us to locate it on the Platform',
              'Your contact information (name, address, telephone number, email)',
              'A statement that you have a good faith belief that use of the material is not authorized by the copyright owner, its agent, or the law',
              'A statement, under penalty of perjury, that the information in the notification is accurate and that you are the copyright owner or authorized to act on the owner\'s behalf',
            ]} />
            <P>We will respond to valid DMCA notices in accordance with applicable law and may remove or disable access to the allegedly infringing material. Repeat infringers may have their accounts terminated.</P>
          </SubSection>
        </Section>

        <Section title="10. Privacy and Data">
          <P>Your use of the Service is subject to our Privacy Policy, which is incorporated into these Terms by reference. By using the Service, you consent to the collection, use, and sharing of your information as described in the Privacy Policy.</P>
          <P>You acknowledge that certain information you provide or that is generated through your use of the Service (including collection data, transaction history, and marketplace activity) may be visible to other users in accordance with your privacy settings and the nature of the Service. Public posts, marketplace listings, and collection data shared through the Hive or Honeypot are visible to all users and may be indexed by search engines.</P>
        </Section>

        <Section title="11. Third-Party Services">
          <P>The Service integrates with and relies upon third-party services, including but not limited to Stripe for payment processing, Cloudinary for image hosting, and the Spotify and Discogs APIs for catalog data and album artwork. Your use of these third-party services is subject to their respective terms of service and privacy policies, which are separate from and in addition to these Terms.</P>
          <P>We are not responsible for the availability, accuracy, or reliability of any third-party service. We are not liable for any loss or damage caused by your use of or reliance on any third-party service. If any third-party service becomes unavailable, we may modify or discontinue related features of the Service without liability.</P>
          <P>Links to third-party websites or resources may be provided on the Platform. We do not endorse and are not responsible for any content, advertising, products, or services available through third-party links. You access third-party links at your own risk.</P>
        </Section>

        <Section title="12. Disclaimers">
          <P className="uppercase text-xs tracking-wide">THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE. TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, THE HONEY GROOVE EXPRESSLY DISCLAIMS ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, NON-INFRINGEMENT, AND ANY WARRANTIES ARISING OUT OF COURSE OF DEALING, USAGE, OR TRADE PRACTICE.</P>
          <P>Without limiting the foregoing, we make no warranty that:</P>
          <UL items={[
            'The Service will meet your requirements or expectations',
            'The Service will be uninterrupted, timely, secure, or error-free',
            'The results obtained from the Service will be accurate, complete, or reliable',
            'Any records purchased, sold, or traded through the Marketplace will be authentic, accurately described, or in the condition represented by the seller',
            'Any catalog data, album artwork, pricing information, or other content displayed on the Platform is accurate or current',
            'The Service will be compatible with your devices, browsers, or operating systems',
          ]} />
          <P>You acknowledge that The Honey Groove is a platform that facilitates connections between vinyl collectors. We do not authenticate, inspect, grade, appraise, or guarantee any records or other items listed on the Platform. All representations about the condition, authenticity, and value of records are made by individual sellers and are not endorsed or verified by The Honey Groove.</P>
        </Section>

        <Section title="13. Limitation of Liability">
          <P className="uppercase text-xs tracking-wide">TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL THE HONEY GROOVE, ITS OFFICERS, DIRECTORS, MEMBERS, MANAGERS, EMPLOYEES, AGENTS, AFFILIATES, SUCCESSORS, OR ASSIGNS (COLLECTIVELY, THE "HONEY GROOVE PARTIES") BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO DAMAGES FOR LOSS OF PROFITS, GOODWILL, USE, DATA, OR OTHER INTANGIBLE LOSSES, REGARDLESS OF WHETHER SUCH DAMAGES ARE BASED ON WARRANTY, CONTRACT, TORT (INCLUDING NEGLIGENCE), STRICT LIABILITY, OR ANY OTHER LEGAL THEORY, AND REGARDLESS OF WHETHER THE HONEY GROOVE PARTIES HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.</P>
          <P className="uppercase text-xs tracking-wide">TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE TOTAL AGGREGATE LIABILITY OF THE HONEY GROOVE PARTIES FOR ALL CLAIMS ARISING OUT OF OR RELATING TO THESE TERMS OR YOUR USE OF THE SERVICE SHALL NOT EXCEED THE GREATER OF (A) THE TOTAL AMOUNT OF FEES PAID BY YOU TO THE HONEY GROOVE DURING THE TWELVE (12) MONTHS IMMEDIATELY PRECEDING THE EVENT GIVING RISE TO THE CLAIM, OR (B) ONE HUNDRED UNITED STATES DOLLARS ($100 USD).</P>
          <P>The Honey Groove Parties are not liable for:</P>
          <UL items={[
            'The condition, authenticity, legality, or quality of any records or items listed, sold, or traded on the Platform',
            'Any disputes between users, including disputes over the condition of records, payment, shipping, or any other aspect of a transaction',
            'Shipping delays, damage during transit, lost packages, or carrier errors',
            'Errors, inaccuracies, or omissions in catalog data, album artwork, pricing information, or other content sourced from third-party APIs',
            'Any unauthorized access to or alteration of your data, transmissions, or account',
            'Any loss of data, including collection data, transaction history, or User Content',
            'Service interruptions, outages, or modifications',
            'Actions or inactions of third-party service providers, including Stripe, Cloudinary, Spotify, or Discogs',
          ]} />
          <P>Some jurisdictions do not allow the exclusion or limitation of certain warranties or liability. In such jurisdictions, the limitations set forth above shall apply to the fullest extent permitted by applicable law.</P>
        </Section>

        <Section title="14. Indemnification">
          <P>You agree to indemnify, defend, and hold harmless The Honey Groove Parties from and against any and all claims, demands, actions, damages, losses, costs, liabilities, and expenses (including reasonable attorneys' fees and court costs) arising out of or relating to:</P>
          <UL items={[
            'Your use of or access to the Service',
            'Your User Content',
            'Your violation of these Terms or any applicable law or regulation',
            'Your violation of any rights of any third party, including intellectual property, privacy, or publicity rights',
            'Any transaction you enter into through the Marketplace, including disputes with other users',
            'Any claim that your User Content caused damage to a third party',
            'Any misrepresentation made by you in connection with a marketplace listing or transaction',
          ]} />
          <P>We reserve the right, at your expense, to assume the exclusive defense and control of any matter for which you are required to indemnify us, and you agree to cooperate with our defense of such claims. You agree not to settle any such matter without our prior written consent.</P>
        </Section>

        <Section title="15. Dispute Resolution and Arbitration">
          <SubSection title="15.1 Informal Resolution">
            <P>Before initiating any formal dispute resolution proceeding, you agree to first contact us at <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> and attempt to resolve the dispute informally for at least 30 days. If we are unable to resolve the dispute informally, either party may proceed as described below.</P>
          </SubSection>
          <SubSection title="15.2 Binding Arbitration">
            <P>Any dispute, controversy, or claim arising out of or relating to these Terms, your use of the Service, or any transaction conducted through the Service that cannot be resolved through informal negotiation shall be resolved exclusively through binding arbitration administered by the American Arbitration Association ("AAA") in accordance with its Consumer Arbitration Rules. The arbitration shall be conducted by a single arbitrator. The seat of arbitration shall be in the State of Georgia, United States, but may be conducted remotely to the extent permitted by the AAA rules.</P>
            <P>The arbitrator's decision shall be final and binding on both parties and may be entered as a judgment in any court of competent jurisdiction. The arbitrator shall have the authority to award any relief that would be available in a court of law. Each party shall bear its own costs and attorneys' fees, unless the arbitrator determines that a claim was frivolous, in which case the arbitrator may award reasonable attorneys' fees to the prevailing party.</P>
          </SubSection>
          <SubSection title="15.3 Class Action Waiver">
            <P className="uppercase text-xs tracking-wide">YOU AND THE HONEY GROOVE AGREE THAT EACH PARTY MAY BRING CLAIMS AGAINST THE OTHER ONLY IN YOUR OR ITS INDIVIDUAL CAPACITY AND NOT AS A PLAINTIFF OR CLASS MEMBER IN ANY PURPORTED CLASS, COLLECTIVE, REPRESENTATIVE, OR CONSOLIDATED ACTION. UNLESS BOTH YOU AND THE HONEY GROOVE AGREE OTHERWISE, THE ARBITRATOR MAY NOT CONSOLIDATE MORE THAN ONE PERSON'S CLAIMS AND MAY NOT OTHERWISE PRESIDE OVER ANY FORM OF A CLASS, COLLECTIVE, OR REPRESENTATIVE PROCEEDING.</P>
          </SubSection>
          <SubSection title="15.4 Exceptions">
            <P>Notwithstanding the above, either party may seek injunctive or other equitable relief in any court of competent jurisdiction to prevent the actual or threatened infringement, misappropriation, or violation of intellectual property rights. Claims eligible for small claims court may also be brought there instead of arbitration.</P>
          </SubSection>
        </Section>

        <Section title="16. Governing Law and Jurisdiction">
          <P>These Terms shall be governed by and construed in accordance with the laws of the State of Georgia, United States of America, without regard to its conflict of law provisions. To the extent that arbitration is not applicable or is deemed unenforceable, you and The Honey Groove irrevocably consent to the exclusive jurisdiction and venue of the state and federal courts located in the State of Georgia for the resolution of any disputes arising out of or relating to these Terms.</P>
        </Section>

        <Section title="17. Termination">
          <SubSection title="17.1 Termination by Us">
            <P>We reserve the right to suspend or terminate your account and access to the Service at any time, with or without cause, and with or without notice, in our sole discretion. Grounds for termination include, but are not limited to:</P>
            <UL items={[
              'Violation of these Terms or any of our policies',
              'Fraudulent, deceptive, or illegal activity',
              'Receiving repeated disputes or complaints from other users',
              'Failure to complete transactions in good faith',
              'Abusive or threatening behavior toward other users or our team',
              'Extended inactivity (accounts inactive for more than 24 months may be subject to deletion)',
              'Any conduct that we determine, in our sole judgment, is harmful to other users, to us, or to the integrity of the Platform',
            ]} />
          </SubSection>
          <SubSection title="17.2 Termination by You">
            <P>You may request account deletion from your profile settings or by contacting <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a> at any time. All active marketplace listings will be deactivated upon account deletion. All pending trades or sales must be completed or cancelled before deletion can be processed. You are responsible for withdrawing any available balance from your Stripe account before requesting deletion.</P>
          </SubSection>
          <SubSection title="17.3 Effects of Termination">
            <P>Upon termination of your account, your right to use the Service immediately ceases. We may retain and continue to use your User Content to the extent licensed under Section 5. Completed transaction history is retained for record-keeping, legal compliance, and dispute resolution purposes. The following provisions survive termination: Sections 5 (User Content), 9 (Intellectual Property), 12 (Disclaimers), 13 (Limitation of Liability), 14 (Indemnification), 15 (Dispute Resolution), 16 (Governing Law), and this Section 17.3.</P>
          </SubSection>
        </Section>

        <Section title="18. General Provisions">
          <SubSection title="18.1 Entire Agreement">
            <P>These Terms, together with the Privacy Policy and any other policies incorporated by reference, constitute the entire agreement between you and The Honey Groove regarding the Service and supersede all prior or contemporaneous agreements, representations, warranties, and understandings, whether written or oral.</P>
          </SubSection>
          <SubSection title="18.2 Severability">
            <P>If any provision of these Terms is found to be unlawful, void, or unenforceable by a court or arbitrator of competent jurisdiction, that provision shall be enforced to the maximum extent permissible, and the remaining provisions shall continue in full force and effect.</P>
          </SubSection>
          <SubSection title="18.3 Waiver">
            <P>Our failure to enforce any right or provision of these Terms shall not constitute a waiver of that right or provision. Any waiver of any provision of these Terms will be effective only if in writing and signed by The Honey Groove.</P>
          </SubSection>
          <SubSection title="18.4 Assignment">
            <P>You may not assign or transfer these Terms or any rights or obligations hereunder without our prior written consent. We may assign these Terms, in whole or in part, without restriction, including in connection with a merger, acquisition, reorganization, or sale of assets.</P>
          </SubSection>
          <SubSection title="18.5 Force Majeure">
            <P>We shall not be liable for any failure or delay in performance of our obligations under these Terms to the extent such failure or delay results from circumstances beyond our reasonable control, including but not limited to natural disasters, acts of war or terrorism, epidemics, pandemics, government actions, power failures, internet or telecommunications failures, or third-party service outages.</P>
          </SubSection>
          <SubSection title="18.6 Notices">
            <P>All notices from The Honey Groove to you will be sent to the email address associated with your account. It is your responsibility to keep your email address current. All notices from you to The Honey Groove should be sent to <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>. Notices are deemed received when sent by email.</P>
          </SubSection>
          <SubSection title="18.7 No Third-Party Beneficiaries">
            <P>These Terms do not create any third-party beneficiary rights in any individual or entity that is not a party to this Agreement.</P>
          </SubSection>
          <SubSection title="18.8 Headings">
            <P>The section headings in these Terms are for convenience only and have no legal or contractual effect.</P>
          </SubSection>
        </Section>

        <Section title="19. Contact Information">
          <P>If you have any questions about these Terms of Service, please contact us:</P>
          <P>Email: <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a><br />Website: <a href="https://thehoneygroove.com" className="text-honey-amber hover:underline">thehoneygroove.com</a></P>
        </Section>

        <p className="text-xs text-vinyl-black/30 text-center mt-8">End of Terms of Service</p>

        <Footer />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <div className="mb-8" data-testid={`terms-section-${title.toLowerCase().replace(/[\s.]+/g, '-')}`}>
    <h2 className="font-heading text-xl text-honey-amber mb-3">{title}</h2>
    {children}
  </div>
);

const SubSection = ({ title, children }) => (
  <div className="mb-4 ml-0">
    <h3 className="font-semibold text-sm text-vinyl-black mb-2">{title}</h3>
    {children}
  </div>
);

const P = ({ children, className = '' }) => (
  <p className={`text-sm text-vinyl-black/70 leading-relaxed mb-3 ${className}`}>{children}</p>
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
      <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Privacy Policy</Link>
      <Link to="/guidelines" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Guidelines</Link>
      <Link to="/faq" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">FAQ</Link>
    </div>
  </div>
);

export default TermsPage;
