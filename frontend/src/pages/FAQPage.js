import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import SEOHead from '../components/SEOHead';

const faqSections = [
  {
    title: 'Getting Started',
    items: [
      {
        q: 'What is The Honey Groove?',
        a: (
          <>
            <p>The Honey Groove is a social platform built specifically for vinyl collectors. Track your collection, share what you're spinning, post your hauls, build a Dream List of records you want, and buy, sell, or trade vinyl directly with other collectors.</p>
            <p className="mt-2">Unlike traditional record marketplaces, The Honey Groove combines collection tracking, community, and a vinyl marketplace in one place.</p>
          </>
        ),
      },
      {
        q: 'Is The Honey Groove free?',
        a: (
          <>
            <p>Yes. The Honey Groove is free to join and use.</p>
            <p className="mt-2">We take a 6% transaction fee on completed sales through The Honeypot marketplace. Trades with no sweetener are free.</p>
            <p className="mt-2">Optional features like Golden Hive ID verification may require a one-time fee.</p>
          </>
        ),
      },
      {
        q: 'Who is The Honey Groove for?',
        a: (
          <>
            <p>Anyone who collects vinyl.</p>
            <p className="mt-2">Casual listeners, obsessive diggers, new collectors, crate diggers, audiophiles, and lifelong collectors. If you care about records, you belong here.</p>
          </>
        ),
      },
      {
        q: 'Is The Honey Groove a Discogs alternative?',
        a: (
          <>
            <p>Yes — but it's more than that.</p>
            <p className="mt-2">Discogs focuses primarily on a database and marketplace. The Honey Groove adds:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>a social feed for vinyl collectors</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>collection discovery</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>Dream Lists and ISO hunting</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>protected record trading</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>variant tracking and collector insights</li>
            </ul>
            <p className="mt-2">Think of it as Discogs + a vinyl social network + a trading marketplace.</p>
          </>
        ),
      },
      {
        q: 'Is there a mobile app?',
        a: (
          <>
            <p>Right now The Honey Groove is a mobile-optimized web app that works beautifully in your phone browser and can be saved to your home screen.</p>
            <p className="mt-2">Native iOS and Android apps are on the roadmap.</p>
          </>
        ),
      },
      {
        q: 'Who built The Honey Groove?',
        a: (
          <>
            <p>The Honey Groove was built by Katie Klodnicki, a vinyl collector and product manager who wanted a better way to manage her collection and connect with other collectors.</p>
            <p className="mt-2">It was built for collectors, by a collector.</p>
          </>
        ),
      },
    ],
  },
  {
    title: 'The Hive',
    items: [
      {
        q: 'What is The Hive?',
        a: (
          <>
            <p>The Hive is the social feed of The Honey Groove.</p>
            <p className="mt-2">Collectors share:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>what they're spinning</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>new vinyl hauls</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>records they're hunting</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>daily prompt responses</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>collector conversations</li>
            </ul>
            <p className="mt-2">It's where the vinyl community comes alive.</p>
          </>
        ),
      },
      {
        q: 'What can I post in The Hive?',
        a: (
          <>
            <p>Collectors typically post:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>Now Spinning</strong> — what you're playing right now</span></li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>New Haul</strong> — a record you just picked up</span></li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>ISO</strong> — a record you're actively searching for</span></li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>Notes</strong> — anything vinyl related</span></li>
            </ul>
          </>
        ),
      },
      {
        q: 'What is the Randomizer?',
        a: (
          <>
            <p>The Randomizer selects a random record from your collection and allows you to instantly share it to The Hive.</p>
            <p className="mt-2">It's a fun way to rediscover records you already own and spark conversation.</p>
            <p className="mt-2">Randomizer posts include a Randomizer tag so others know it was randomly selected.</p>
          </>
        ),
      },
      {
        q: 'What is the Daily Prompt?',
        a: (
          <>
            <p>Every day The Honey Groove asks the community a vinyl question.</p>
            <p className="mt-2">Examples include:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>"What record would you save in a fire?"</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>"What's spinning right now?"</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>"Your favorite album closer?"</li>
            </ul>
            <p className="mt-2">Tap Buzz In and answer using a record from your collection.</p>
          </>
        ),
      },
      {
        q: 'What is a Buzz In streak?',
        a: (
          <>
            <p>Answer the Daily Prompt consistently and build a streak.</p>
            <p className="mt-2">Your streak appears on your profile with a bee icon.</p>
            <p className="mt-2">Miss a day and the streak resets.</p>
          </>
        ),
      },
    ],
  },
  {
    title: 'Collection',
    items: [
      {
        q: 'How do I add records to my collection?',
        a: (
          <>
            <p>Search by artist or album and we pull artwork and metadata automatically from Discogs.</p>
            <p className="mt-2">Records are saved using the exact Discogs release ID, so variants and pressings are accurate.</p>
          </>
        ),
      },
      {
        q: 'Can I import my Discogs collection?',
        a: 'Yes. Enter your Discogs username and we\'ll import your entire collection automatically.',
      },
      {
        q: 'Does The Honey Groove sync with Discogs?',
        a: 'Yes. You can import your Discogs collection, and records added to your Honey Groove collection can also sync back to Discogs.',
      },
      {
        q: 'How is my collection value calculated?',
        a: (
          <>
            <p>Your collection value is calculated using Discogs median sale prices for each variant.</p>
            <p className="mt-2">Values update regularly as market data changes.</p>
          </>
        ),
      },
      {
        q: 'Can I track specific variants or pressings?',
        a: (
          <>
            <p>Yes.</p>
            <p className="mt-2">Each record can include:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>vinyl color or variant</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>label</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>catalog number</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>pressing country</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>release year</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>condition notes</li>
            </ul>
          </>
        ),
      },
    ],
  },
  {
    title: 'Dream List',
    items: [
      {
        q: 'What is the Dream List?',
        a: (
          <>
            <p>Your Dream List is a list of records you'd love to own someday.</p>
            <p className="mt-2">Each Dream record shows the Discogs median market value, and the top of the page displays the total value of your dream records.</p>
          </>
        ),
      },
      {
        q: 'What is Actively Seeking?',
        a: (
          <>
            <p>Actively Seeking is your ISO list.</p>
            <p className="mt-2">Records moved here appear in the marketplace so other collectors know you're actively looking for them.</p>
          </>
        ),
      },
      {
        q: 'Can I move a Dream record into my collection?',
        a: 'Yes. If you obtain a Dream record, simply tap Add to Collection and it will move from your Dream List to your collection.',
      },
    ],
  },
  {
    title: 'The Honeypot Marketplace',
    items: [
      {
        q: 'What is The Honeypot?',
        a: (
          <>
            <p>The Honeypot is the marketplace inside The Honey Groove.</p>
            <p className="mt-2">It includes three sections:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>Shop</strong> — buy and sell records</span></li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>Seeking</strong> — browse what collectors are actively seeking</span></li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span><span><strong>Trade</strong> — swap records with other collectors</span></li>
            </ul>
          </>
        ),
      },
      {
        q: 'Can I buy and sell vinyl records?',
        a: 'Yes. Collectors can list records for sale and receive payouts directly through Stripe.',
      },
      {
        q: 'What are the marketplace fees?',
        a: (
          <>
            <p>The Honey Groove charges 6% on completed sales.</p>
            <p className="mt-2">Trades with a sweetener are charged 6% on the sweetener amount only.</p>
          </>
        ),
      },
    ],
  },
  {
    title: 'Shipping, Ratings, and Disputes',
    items: [
      {
        q: 'How long do I have to ship a record after a sale or trade?',
        a: 'After a sale or accepted trade, the seller must ship the record within 5 days and enter a valid tracking number.',
      },
      {
        q: 'What happens after delivery?',
        a: (
          <>
            <p>Once a shipment is marked Delivered, a confirmation window begins.</p>
            <p className="mt-2">Both parties can confirm the transaction and leave ratings.</p>
          </>
        ),
      },
      {
        q: 'How long do I have to rate a buyer or seller?',
        a: (
          <>
            <p>After delivery:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>Buyers have 48 hours to rate the seller</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>Sellers have 48 hours to rate the buyer</li>
            </ul>
            <p className="mt-2">If neither party leaves a rating within 48 hours, the transaction automatically closes.</p>
          </>
        ),
      },
      {
        q: 'How long do I have to confirm a trade?',
        a: (
          <>
            <p>For trades, both collectors have 24 hours after delivery to confirm receipt.</p>
            <p className="mt-2">If neither user confirms within 24 hours, the trade automatically completes and holds are released.</p>
          </>
        ),
      },
      {
        q: "What if someone doesn't ship their record?",
        a: 'If tracking is not entered within 5 days, the transaction can be cancelled and any held funds are released.',
      },
      {
        q: "What if I receive a record that isn't as described?",
        a: (
          <>
            <p>You can open a dispute within 48 hours of delivery.</p>
            <p className="mt-2">Upload photos and describe the issue so our team can review it.</p>
          </>
        ),
      },
    ],
  },
  {
    title: 'Trades',
    items: [
      {
        q: 'How does trading work?',
        a: (
          <>
            <p>Collectors propose trades using records from their collection.</p>
            <p className="mt-2">Once both parties accept:</p>
            <ul className="mt-2 space-y-1 pl-4">
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>a Mutual Hold is placed</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>both collectors ship within 5 days</li>
              <li className="flex items-start gap-2"><span className="text-honey-amber mt-1.5 shrink-0">•</span>delivery triggers a 24-hour confirmation window</li>
            </ul>
          </>
        ),
      },
      {
        q: 'What is a Mutual Hold?',
        a: (
          <>
            <p>A Mutual Hold is a temporary hold placed on both collectors' payment methods equal to the estimated Discogs value of the records.</p>
            <p className="mt-2">This protects both sides and prevents scams.</p>
          </>
        ),
      },
    ],
  },
  {
    title: 'Safety and Trust',
    items: [
      {
        q: 'What is Golden Hive ID?',
        a: (
          <>
            <p>Golden Hive ID is a verified collector badge.</p>
            <p className="mt-2">Collectors who complete identity verification receive a badge that appears on their profile, listings, and trades.</p>
            <p className="mt-2">Verification helps other collectors know they are dealing with a trusted member of the community.</p>
          </>
        ),
      },
      {
        q: 'Can I block someone?',
        a: 'Yes. Blocked users cannot view your profile, message you, or interact with your posts.',
      },
      {
        q: 'Is my payment information safe?',
        a: (
          <>
            <p>All payments are processed through Stripe, which is PCI-DSS compliant.</p>
            <p className="mt-2">The Honey Groove never stores your payment information.</p>
          </>
        ),
      },
      {
        q: 'Does The Honey Groove run ads?',
        a: (
          <>
            <p>No.</p>
            <p className="mt-2">The Honey Groove is ad-free. The platform earns revenue through transaction fees, not advertising.</p>
          </>
        ),
      },
    ],
  },
];

const FAQItem = ({ q, a }) => {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen(!open)}
      className="w-full text-left py-4 border-b border-honey/20 group"
      data-testid={`faq-item-${q.substring(0, 20).replace(/\s+/g, '-').toLowerCase()}`}
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-medium text-vinyl-black text-sm md:text-base pr-4">{q}</h3>
        <ChevronDown className={`w-4 h-4 text-honey-amber shrink-0 mt-1 transition-transform ${open ? 'rotate-180' : ''}`} />
      </div>
      {open && (
        <div className="text-sm text-vinyl-black/70 mt-3 leading-relaxed pr-8">
          {typeof a === 'string' ? <p>{a}</p> : a}
        </div>
      )}
    </button>
  );
};

const FAQPage = () => {
  usePageTitle('FAQ');
  return (
  <div className="min-h-screen bg-honey-cream">
    <SEOHead
      title="FAQ — Frequently Asked Questions"
      description="Everything you need to know about The Honey Groove — the social marketplace for vinyl collectors."
      url="/faq"
    />
    <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="faq-page">
      <h1 className="font-heading text-4xl text-vinyl-black mb-2">FAQ</h1>
      <p className="text-muted-foreground mb-10">Everything you need to know about The Honey Groove — the social marketplace for vinyl collectors.</p>

      {faqSections.map(section => (
        <div key={section.title} className="mb-8" data-testid={`faq-section-${section.title.toLowerCase().replace(/\s+/g, '-')}`}>
          <h2 className="font-heading text-xl text-honey-amber mb-1">{section.title}</h2>
          <div>
            {section.items.map(item => (
              <FAQItem key={item.q} q={item.q} a={item.a} />
            ))}
          </div>
        </div>
      ))}

      <div className="mt-12 text-center bg-honey/10 rounded-2xl p-8 border border-honey/20">
        <h2 className="font-heading text-2xl text-vinyl-black mb-2">Still have questions?</h2>
        <p className="text-sm text-vinyl-black/70">
          Slide into our DMs at <strong>@thehoneygroove</strong> or drop us a note at{' '}
          <a href="mailto:hello@thehoneygroove.com" className="text-honey-amber hover:underline">hello@thehoneygroove.com</a>.
          <br />We're collectors too. We get it.
        </p>
      </div>

      <div className="mt-12 pt-8 border-t border-honey/20 flex items-center justify-between">
        <Link to="/" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Back to Home</Link>
        <div className="flex gap-4">
          <Link to="/terms" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Terms</Link>
          <Link to="/privacy" className="text-sm text-vinyl-black/50 hover:text-honey-amber transition-colors">Privacy Policy</Link>
        </div>
      </div>
    </div>
  </div>
  );
};

export default FAQPage;
