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
        q: 'What is the Honey Groove?',
        a: 'The Honey Groove is a social app built specifically for vinyl collectors. Track your collection, share what you\'re spinning, post your hauls, hunt down records on your wantlist, and buy, sell, and trade directly with other collectors who get it.',
      },
      {
        q: 'Is it free?',
        a: 'Yes. The Honey Groove is free to join and use. We take a small 6% transaction fee on completed sales through The Honeypot marketplace. Trades with no sweetener are free.',
      },
      {
        q: 'Who is it for?',
        a: 'Anyone who collects vinyl. Casual listeners, obsessive diggers, new collectors, lifers. If you care about records, you belong here.',
      },
      {
        q: 'How do I get access right now?',
        a: 'The Honey Groove is currently in closed beta. Join the waitlist at thehoneygroove.com/beta and we\'ll send you an invite when your spot is ready. Founding members get a permanent badge on their profile that never goes away.',
      },
      {
        q: 'Is there a mobile app?',
        a: 'Right now the Honey Groove is a fully mobile-optimized web app \u2014 it works beautifully in your phone browser and can be saved to your home screen. A native iOS and Android app is on the roadmap.',
      },
      {
        q: 'Who built the Honey Groove?',
        a: 'The Honey Groove was built by Katie Klodnicki, a vinyl collector and product manager who got tired of managing her collection across five different apps and none of them feeling like home. It was built for collectors, by a collector.',
      },
      {
        q: 'Is my data private?',
        a: 'Yes. We never sell your data, share it with third parties for advertising, or use it for anything beyond making your experience better. Your collection, your wantlist, and your listening history are yours.',
      },
    ],
  },
  {
    title: 'The Hive',
    items: [
      {
        q: 'What is The Hive?',
        a: 'The Hive is your social feed. It\'s where the community lives. You\'ll see what people are spinning, what they just found, what they\'re searching for, and anything else collectors want to share.',
      },
      {
        q: 'What can I post?',
        a: 'Four things. Now Spinning when you drop the needle \u2014 optionally attach a Vinyl Mood if a record is a whole feeling. New Haul when you score something good. ISO when you\'re searching for something specific. A Note for anything else on your mind.',
      },
      {
        q: 'What is a Vinyl Mood?',
        a: 'A Vinyl Mood is a feeling you attach to a Now Spinning post. Twelve moods to choose from \u2014 Late Night, Nostalgic, Euphoric, Melancholic, and more. It tells the community not just what you\'re playing but how it\'s making you feel.',
      },
      {
        q: 'What is the Daily Prompt?',
        a: 'Every day the Honey Groove drops a question for the community \u2014 things like "the record you\'d save in a fire" or "what\'s on right now, no context." Tap buzz in to answer with a record from your collection. Answers show up in The Hive feed and can be shared to Instagram Stories.',
      },
      {
        q: 'What is a buzz in streak?',
        a: 'Answer the daily prompt every day and build a streak. Your streak count shows on your profile with a 🐝 bee icon. Miss a day and it resets. The longer your streak the more the community notices.',
      },
      {
        q: 'Can I see posts from everyone or just people I follow?',
        a: 'The Hive shows posts from the entire community so it feels alive from day one. As the community grows we\'ll be adding a Friends view to filter by people you follow.',
      },
      {
        q: 'Can I comment on posts?',
        a: 'Yes. Every post in The Hive is commentable, likeable, and shareable. Tap the comment icon on any post to join the conversation.',
      },
      {
        q: 'Can I share posts to Instagram?',
        a: 'Yes. Now Spinning, New Haul, and Daily Prompt posts can all be exported as Instagram Story cards directly from the app. One tap generates a beautifully designed card with your album art, stats, and handle ready to share.',
      },
    ],
  },
  {
    title: 'Collection',
    items: [
      {
        q: 'How do I add records to my collection?',
        a: 'Search by artist or album and we pull in album art and details automatically from Discogs. You can add press information, condition notes, and personal ratings for each record.',
      },
      {
        q: 'Can I import my Discogs collection?',
        a: 'Yes. Enter your Discogs username and we\'ll import your entire collection in one go. Duplicate records are handled automatically. Your collection value is calculated immediately after import using current Discogs market data.',
      },
      {
        q: 'Is my collection public?',
        a: 'Yes by default. Other collectors can browse your collection from your profile. You can make individual records private from your collection settings if you prefer.',
      },
      {
        q: 'How is my collection value calculated?',
        a: 'We pull current market data from Discogs and calculate the estimated value of your collection based on recent median sale prices. Your total collection value is visible on your profile and updated regularly. Individual record values are shown on each record in your collection.',
      },
      {
        q: 'Can I add condition notes to my records?',
        a: 'Yes. Each record in your collection has a condition field where you can note the grade of both the vinyl and the sleeve. This is especially useful when listing records for sale or trade.',
      },
      {
        q: 'Can I rate records in my collection?',
        a: 'Yes. You can add a personal rating to any record in your collection. Your ratings are visible on your profile and help other collectors understand your taste.',
      },
      {
        q: 'What pressing information can I track?',
        a: 'You can note the pressing country, label, catalog number, color or variant, and any other details specific to your copy. The more detail you add the more useful your collection becomes for trading.',
      },
    ],
  },
  {
    title: 'The Wantlist',
    items: [
      {
        q: 'What is the Wantlist?',
        a: 'Your Wantlist is your hunt list. Add any record you\'ve been looking for and we\'ll notify you the moment another collector lists it in The Honeypot. You can specify pressing preferences and condition requirements for each entry.',
      },
      {
        q: 'What happens when someone lists a record on my Wantlist?',
        a: 'You get an instant notification \u2014 in-app and by email \u2014 with a direct link to the listing. Wantlist matches move fast so we flag them the moment they appear.',
      },
      {
        q: 'Can other collectors see my Wantlist?',
        a: 'Yes. Your Wantlist is visible on your profile. Other collectors browsing your ISO posts can see what you\'re hunting and reach out directly if they have something you need.',
      },
      {
        q: 'Can I set a price limit on a Wantlist entry?',
        a: 'Yes. You can set a maximum price for each Wantlist entry. We\'ll only notify you when a matching listing appears at or below your target price so you\'re not pinged for listings out of your budget.',
      },
      {
        q: 'How long do Wantlist entries stay active?',
        a: 'Indefinitely. Your Wantlist entries stay active until you remove them manually. We\'ll keep hunting until you find what you\'re looking for.',
      },
      {
        q: 'Can I add pressing-specific requirements to my Wantlist?',
        a: 'Yes. For each entry you can specify the pressing country, label, variant, or color you\'re looking for. We\'ll match based on your requirements and only notify you when the right copy appears.',
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
        a: 'Any collector with a connected Stripe account. You\'ll need to verify through Stripe before your first listing goes live. It takes about two minutes and your earnings are paid directly to your bank account.',
      },
      {
        q: 'What are the fees?',
        a: 'The Honey Groove charges a 6% fee on completed sales \u2014 lower than any major vinyl marketplace. If your trade includes a sweetener we take 6% of the sweetener amount only. The Mutual Hold amount is fully reversed on completion and is not subject to any fee.',
      },
      {
        q: 'What is a sweetener?',
        a: 'A sweetener is cash added to a trade to balance an unequal swap. If you want to trade your copy of Blue for someone\'s copy of Rumours you might add a sweetener to make it fair. Both parties agree on the amount before the trade locks in.',
      },
      {
        q: 'What condition are records listed in?',
        a: 'Every listing requires a condition rating \u2014 Mint, Near Mint, Very Good Plus, Very Good, or Good \u2014 and at least one photo of the actual record including the sleeve, labels, and any wear. What you see is what you get.',
      },
      {
        q: 'How does shipping work?',
        a: 'Both parties ship within 5 days of a completed sale or accepted trade. Tracking numbers are required and entered inside the app. We show live tracking status to both parties so everyone knows where things stand.',
      },
      {
        q: 'When do sellers get paid?',
        a: 'Seller payouts are held for 5 days after delivery confirmation. This gives buyers a window to flag any issues before funds are released. Once the hold period passes with no dispute the payout is transferred to the seller\'s connected Stripe account within 2 to 5 business days.',
      },
      {
        q: 'What if something goes wrong with my order?',
        a: 'You have 48 hours after delivery confirmation to flag a dispute. Upload photos and describe the issue. We review every dispute and will always make it right. For high value items where fraud is clear we will remove the seller from the platform, provide documentation to support a payment dispute with your card issuer, and work with you directly to find a resolution.',
      },
      {
        q: 'What if I get scammed during a trade?',
        a: 'We take fraud seriously and have protections in place on both sides. If you receive a record that is significantly not as described file a dispute within 48 hours of delivery with photos of what you received. If the other party never ships you can cancel the trade after 5 days and any sweetener payments will be refunded. Never send money outside the Honey Groove \u2014 any seller asking you to pay via Venmo, PayPal, Zelle, or any other outside method is not legitimate. All transactions happen inside the app through Stripe only. Report any suspicious behavior immediately using the report button on their profile.',
      },
      {
        q: 'Does shipping insurance matter?',
        a: 'For items over $75 we strongly recommend sellers add shipping insurance. Listings show whether the seller has added insurance so you know before you buy. If a record is lost or damaged in transit with no insurance resolution options are more limited \u2014 insurance protects both parties.',
      },
      {
        q: 'Can I make an offer below the asking price?',
        a: 'Yes on listings marked Make an Offer. The seller can accept, counter, or decline. On Buy It Now listings the price is fixed.',
      },
      {
        q: 'Can I see a seller\'s history before buying?',
        a: 'Yes. Every seller profile shows their completed transaction count, star rating, and member since date. New sellers with fewer than 3 completed transactions cannot list items over $150 until they\'ve built a track record.',
      },
    ],
  },
  {
    title: 'Trades',
    items: [
      {
        q: 'How does a trade work?',
        a: 'Find a listing marked for trade, propose an offer from your own collection, and optionally add a sweetener. Both parties agree on a Mutual Hold amount. Once both sides accept the hold is charged, records are locked, and both parties ship within 5 days. After both deliveries are confirmed and both parties confirm receipt the holds are fully reversed.',
      },
      {
        q: 'What is a Mutual Hold?',
        a: 'Every trade on the Honey Groove requires a Mutual Hold. Both parties are charged a hold amount equal to the estimated value of the records being traded. The hold sits with the platform and is fully reversed within 24 hours of both parties confirming receipt. It protects both sides \u2014 nobody walks away ahead by scamming because their hold covers the value of what they took.',
      },
      {
        q: 'How is the hold amount calculated?',
        a: 'We suggest a hold amount based on the Discogs median sale price of both records being traded, averaged together. You can adjust the amount but the minimum is $10. Both parties must agree on the hold amount before the trade locks in.',
      },
      {
        q: 'What if I don\'t confirm receipt within 24 hours?',
        a: 'If you don\'t confirm or dispute within 24 hours of delivery confirmation your hold is automatically reversed. This protects you from being held hostage by an unresponsive counterparty.',
      },
      {
        q: 'What if the other person doesn\'t ship?',
        a: 'If either party hasn\'t entered a tracking number within 5 days the other can trigger a cancellation. Both holds are reversed and the trade is voided.',
      },
      {
        q: 'Can I cancel a trade after accepting?',
        a: 'Once both parties have accepted and holds have been charged cancellation requires a dispute. We take this seriously because it protects both sides equally.',
      },
      {
        q: 'What if I receive a record that isn\'t as described?',
        a: 'File a dispute within 48 hours of delivery confirmation. Both holds are frozen immediately. Upload photos showing the condition you received versus what was listed. We review every dispute and resolve within 48 hours.',
      },
    ],
  },
  {
    title: 'The Weekly Wax',
    items: [
      {
        q: 'What is the Week in Wax?',
        a: 'Every Sunday your Week in Wax report is generated \u2014 a full breakdown of your listening week. Top artists, total spins, moods, era breakdown, and a personally generated closing line that captures the vibe of your week in one sentence. Shareable to Instagram Stories as a beautifully designed card.',
      },
      {
        q: 'What is the personality label?',
        a: 'Each Week in Wax includes a personality label generated from your listening data \u2014 things like "a late night listener with a weakness for heartbreak pop" or "a 2020s maximalist who only trusts music that makes her chest hurt a little." You can regenerate it once per week if you want a different one.',
      },
      {
        q: 'What is Collector Bingo?',
        a: 'A new bingo card drops every Friday with 24 collector scenarios based on your week \u2014 things like "spun the same record twice in one day" or "stayed up past midnight listening." Check off the ones that apply, get a bingo, share your card. The card locks Sunday at midnight and a new one drops the following Friday.',
      },
      {
        q: 'What is the Mood Board?',
        a: 'Every Sunday the app automatically generates a 3x3 grid of your most spun album covers from the week. One tap shares it to Instagram Stories or The Hive feed. Zero effort, always beautiful.',
      },
      {
        q: 'Can I look back at old Weekly Wax reports?',
        a: 'Yes. Every report is saved permanently to your profile. Browse all past weekly reports from your profile page \u2014 your listening history going back as far as you\'ve been on the Honey Groove.',
      },
    ],
  },
  {
    title: 'Account and Safety',
    items: [
      {
        q: 'How do I verify my account?',
        a: 'Seller verification happens through Stripe when you connect your payout account. Buyers don\'t need to verify beyond a standard email signup.',
      },
      {
        q: 'What is the rating system?',
        a: 'After every completed trade or sale both parties rate each other out of 5 stars. Ratings are mandatory before your next transaction. Seller ratings and completed transaction counts are visible on every profile and listing so you always know who you\'re dealing with.',
      },
      {
        q: 'Can I block someone?',
        a: 'Yes. Block any user from their profile. Blocked users cannot view your profile, message you, or interact with your posts or listings.',
      },
      {
        q: 'How do I report someone?',
        a: 'Tap the three dot menu on any post, listing, or profile and select Report. Choose a reason and submit. Every report is reviewed by our team. For urgent safety concerns use the report button and we will prioritize your case.',
      },
      {
        q: 'What is a Founding Member?',
        a: 'The first 50 users to join the Honey Groove receive a permanent Founding Member badge on their profile. It shows up next to your handle everywhere in the app and never goes away. You were here first and that means something.',
      },
      {
        q: 'Can I change my username?',
        a: 'Yes. You can update your handle from your profile settings. Your old handle is released and available for others to claim so choose carefully.',
      },
      {
        q: 'What happens if I forget my password?',
        a: 'Use the Forgot Password link on the login screen. We\'ll send a reset link to your email address. If you don\'t receive it check your spam folder.',
      },
      {
        q: 'Can I delete my account?',
        a: 'Yes. You can request account deletion from your profile settings. Deleting your account removes your profile, posts, and collection from the app. Completed transaction history is retained for dispute resolution purposes. Active trades or sales must be completed or cancelled before deletion.',
      },
      {
        q: 'Is my payment information safe?',
        a: 'All payments are processed through Stripe. We never store your card or bank details. Stripe is PCI-DSS compliant and used by millions of businesses worldwide.',
      },
      {
        q: 'Does the Honey Groove run ads?',
        a: 'No. The Honey Groove is ad-free. We make money through transaction fees only, not by selling your attention or your data.',
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

const FAQPage = () => {
  usePageTitle('FAQ');
  return (
  <div className="min-h-screen bg-honey-cream">
    <SEOHead
      title="FAQ — Frequently Asked Questions"
      description="Everything you need to know about The Honey Groove. How to join, how the marketplace works, Discogs integration, and more."
      url="/faq"
    />
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
