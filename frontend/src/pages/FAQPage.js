import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';

const faqSections = [
  {
    title: 'Getting Started',
    items: [
      {
        q: 'What is the Honey Groove?',
        a: 'The Honey Groove is a social app built specifically for vinyl collectors. You can track your collection, share what you\'re spinning, post your hauls, hunt down records on your wantlist, and buy, sell, and trade directly with other collectors.',
      },
      {
        q: 'Is it free?',
        a: 'Yes. The Honey Groove is free to join and use. We take a small transaction fee on completed sales through The Honeypot marketplace.',
      },
      {
        q: 'Who is it for?',
        a: 'Anyone who collects vinyl. Casual listeners, obsessive diggers, new collectors, lifers. If you care about records, you belong here.',
      },
    ],
  },
  {
    title: 'The Hive',
    items: [
      {
        q: 'What is The Hive?',
        a: 'The Hive is your social feed. It\'s where the community lives. You\'ll see what people are spinning, what they just found, what they\'re searching for, and what kind of vinyl mood they\'re in.',
      },
      {
        q: 'What can I post?',
        a: 'Four things. Now Spinning when you drop the needle. New Haul when you score something good. ISO when you\'re searching for something specific. Vinyl Mood when a record is a whole feeling and you want your people to know.',
      },
      {
        q: 'Can I see posts from everyone or just people I follow?',
        a: 'Both. The Hive shows all posts by default so it feels alive from day one. You can switch to a Friends view to see only people you follow once you\'ve built your network.',
      },
    ],
  },
  {
    title: 'Collection',
    items: [
      {
        q: 'How do I add records to my collection?',
        a: 'Search by artist or album and we pull in album art and details automatically. You can add press information, condition notes, and personal ratings for each record.',
      },
      {
        q: 'Can I import my Discogs collection?',
        a: 'We\'re working on a Discogs import feature. It\'s coming soon.',
      },
      {
        q: 'Is my collection public?',
        a: 'Yes by default. Other collectors can browse your collection from your profile. You can make individual records private if you prefer.',
      },
    ],
  },
  {
    title: 'The Wantlist',
    items: [
      {
        q: 'What is the Wantlist?',
        a: 'Your Wantlist is your search list. Add any record you\'ve been looking for and we\'ll notify you the moment another collector lists it in The Honeypot. You can specify press preferences and condition requirements for each entry.',
      },
      {
        q: 'What happens when someone has a record on my Wantlist?',
        a: 'You get an in-app notification immediately and the listing appears at the top of your Honeypot feed under ISO Matches.',
      },
      {
        q: 'Can other collectors see my Wantlist?',
        a: 'Yes. That\'s part of what makes it powerful. Another collector might see your Wantlist, realize they have it sitting in a box, and reach out directly.',
      },
    ],
  },
  {
    title: 'The Honeypot',
    items: [
      {
        q: 'What is The Honeypot?',
        a: 'The Honeypot is our peer-to-peer marketplace. Three tabs: Shop for buying and selling, ISO for browsing the community wantlist, and Trade for swapping records directly with other collectors.',
      },
      {
        q: 'Who can sell?',
        a: 'Any verified collector. You\'ll need to connect a Stripe account before you can list. It takes about two minutes.',
      },
      {
        q: 'What are the fees?',
        a: 'We take 4% on completed sales. Trades with no cash component are free. If your trade includes a sweetener (cash added to balance an unequal swap) we take 4% of the sweetener amount only.',
      },
      {
        q: 'What is a sweetener?',
        a: 'A sweetener is cash added to a trade to make up the difference in value between two records. If you want to trade your copy of Blue for someone\'s copy of Rumours, you\'d add a sweetener to sweeten the deal. Both parties agree on the amount before the trade is locked in.',
      },
      {
        q: 'How does shipping work?',
        a: 'Both parties ship within 5 days of a completed sale or accepted trade. Tracking numbers are required and entered inside the app. We monitor both tracking numbers and show live status to both parties.',
      },
      {
        q: 'What if something goes wrong?',
        a: 'You have 48 hours after delivery confirmation to flag a dispute. Upload photos and describe the issue. We review every dispute and will always make it right.',
      },
    ],
  },
  {
    title: 'Trades',
    items: [
      {
        q: 'How does a trade work?',
        a: 'You find a listing marked for trade, propose an offer from your own collection, and optionally add a sweetener. The other collector accepts, counters, or declines. Once both sides agree the records are locked and both parties ship within 5 days. After both deliveries are confirmed the records transfer to each other\'s collections in the app automatically.',
      },
      {
        q: 'What if the other person doesn\'t ship?',
        a: 'If either party hasn\'t entered a tracking number within 5 days the other can trigger a cancellation. Both records are released and the trade is voided.',
      },
      {
        q: 'Can I cancel a trade after accepting?',
        a: 'Once both parties have accepted, cancellation requires a dispute. We take this seriously because it protects both sides.',
      },
    ],
  },
  {
    title: 'Account and Safety',
    items: [
      {
        q: 'How do I verify my account?',
        a: 'Seller verification happens through Stripe Identity when you connect your account. Buyers don\'t need to verify beyond a standard email signup.',
      },
      {
        q: 'What is the rating system?',
        a: 'After every completed trade or sale both parties rate each other. Ratings are mandatory before your next transaction. Seller ratings are visible on every profile and listing so you always know who you\'re dealing with.',
      },
      {
        q: 'Can I block someone?',
        a: 'Yes. You can block any user from their profile. Blocked users cannot view your profile, message you, or interact with your posts.',
      },
      {
        q: 'Is my payment information safe?',
        a: 'All payments are processed through Stripe. We never store your card or bank details.',
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
        <p className="text-sm text-vinyl-black/70 mt-3 leading-relaxed pr-8">{a}</p>
      )}
    </button>
  );
};

const FAQPage = () => (
  <div className="min-h-screen bg-honey-cream">
    <div className="max-w-2xl mx-auto px-4 py-12 pt-28 pb-24" data-testid="faq-page">
      <h1 className="font-heading text-4xl text-vinyl-black mb-2">FAQ</h1>
      <p className="text-muted-foreground mb-10">everything you need to know about the Honey Groove.</p>

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
    </div>
  </div>
);

export default FAQPage;
