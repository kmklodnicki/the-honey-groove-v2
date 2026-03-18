import React, { useState } from 'react';
import { CreditCard, Zap, Shield, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { usePageTitle } from '../hooks/usePageTitle';

const FAQ_ITEMS = [
  {
    q: 'What is THG Gold?',
    a: 'THG Gold is a monthly membership that gives you lower fees, early access to the Honeypot marketplace, and a Gold badge on all your listings.',
  },
  {
    q: 'When does the Honeypot open?',
    a: 'The Honeypot is almost ready. Gold members will be the first to know — and the first to get in.',
  },
  {
    q: 'Do Gold members get early access?',
    a: 'Yes. When the Honeypot launches, Gold members get access before the general rollout.',
  },
];

const FaqItem = ({ q, a }) => {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="border border-[#F5E6CC] rounded-xl overflow-hidden"
      data-testid={`faq-item-${q.slice(0, 10).replace(/\s/g, '-').toLowerCase()}`}
    >
      <button
        className="w-full flex items-center justify-between px-5 py-4 text-left text-[#2A1A06] font-medium hover:bg-[#FFF8EE] transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span>{q}</span>
        {open ? <ChevronUp className="w-4 h-4 text-[#C8861A] shrink-0" /> : <ChevronDown className="w-4 h-4 text-[#C8861A] shrink-0" />}
      </button>
      {open && (
        <div className="px-5 pb-4 text-sm text-[#8A6B4A]">{a}</div>
      )}
    </div>
  );
};

const GoldPage = () => {
  usePageTitle('THG Gold');

  return (
    <div className="max-w-[680px] mx-auto px-4 py-8 pb-24" data-testid="gold-page">

      {/* Hero */}
      <div className="text-center mb-10">
        <h1
          className="text-[34px] md:text-[42px] font-bold mb-3 leading-tight"
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            background: 'linear-gradient(135deg, #C8861A 0%, #DAA520 50%, #E8A820 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
          data-testid="gold-headline"
        >
          The Honey Groove Gold
        </h1>
        <p className="text-[16px] text-[#8A6B4A]" style={{ fontFamily: 'Georgia, serif' }}>
          Lower fees. Early access. Gold everywhere.
        </p>
      </div>

      {/* Benefits */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          {
            icon: CreditCard,
            title: '4% Fees',
            body: 'Standard members pay 6%. Gold members pay 4% — the lowest rate we offer.',
          },
          {
            icon: Zap,
            title: 'Early Honeypot Access',
            body: 'Shop, sell, and trade before the marketplace opens to everyone.',
          },
          {
            icon: Shield,
            title: 'Gold Badge on Listings',
            body: 'A verified Gold badge on every listing you post. Build trust instantly.',
          },
        ].map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="bg-white border border-[#F5E6CC] rounded-xl p-6 shadow-sm"
            data-testid={`gold-benefit-${title.toLowerCase().replace(/\s/g, '-')}`}
          >
            <Icon className="w-6 h-6 text-[#C8861A] mb-3" />
            <p className="font-bold text-[#2A1A06] mb-1">{title}</p>
            <p className="text-sm text-[#8A6B4A]">{body}</p>
          </div>
        ))}
      </div>

      {/* Pricing card */}
      <div className="max-w-sm mx-auto border-2 border-[#DAA520] rounded-2xl p-8 text-center mb-8 bg-gradient-to-br from-[#FFF9E6] to-[#FFF3E0]" data-testid="gold-pricing-card">
        <p
          className="text-[42px] font-bold text-[#2A1A06] mb-1"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          $4.99
        </p>
        <p className="text-sm text-[#8A6B4A] mb-6">per month</p>
        <ul className="text-left space-y-3 mb-6">
          {[
            '4% marketplace fees (vs 6% standard)',
            'Early Honeypot access',
            'Gold badge on all your listings',
            'Priority matching on Dream List',
          ].map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-[#2A1A06]">
              <CheckCircle2 className="w-4 h-4 text-[#C8861A] mt-0.5 shrink-0" />
              {item}
            </li>
          ))}
        </ul>
        <Button
          className="w-full rounded-full font-bold text-[#2A1A06] mb-2"
          style={{ background: '#E8A820' }}
          onClick={() => toast.info('Gold subscriptions coming soon — stay tuned!')}
          data-testid="gold-subscribe-btn"
        >
          Subscribe
        </Button>
        <p className="text-xs text-[#8A6B4A]">Cancel anytime.</p>
      </div>

      {/* FAQ */}
      <div className="space-y-3" data-testid="gold-faq">
        <h2
          className="font-bold text-[#2A1A06] text-lg mb-4"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Questions
        </h2>
        {FAQ_ITEMS.map((item) => (
          <FaqItem key={item.q} {...item} />
        ))}
      </div>
    </div>
  );
};

export default GoldPage;
