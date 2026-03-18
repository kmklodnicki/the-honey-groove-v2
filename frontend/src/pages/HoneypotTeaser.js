import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ShoppingBag, ArrowRightLeft, Search, CheckCircle2, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';

const HoneypotTeaser = () => {
  usePageTitle('The Honeypot');
  const { user, token, API, updateUser } = useAuth();
  const navigate = useNavigate();
  const [notifying, setNotifying] = useState(false);
  const [animated, setAnimated] = useState(false);

  // Fee bar animation
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(t);
  }, []);

  // Fire-and-forget view tracking
  useEffect(() => {
    if (token) {
      axios
        .post(`${API}/honeypot/view`, {}, { headers: { Authorization: `Bearer ${token}` } })
        .catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleNotify = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setNotifying(true);
    try {
      await axios.post(`${API}/honeypot/notify`, {}, { headers: { Authorization: `Bearer ${token}` } });
      updateUser({ honeypot_notify_me: true });
      toast.success("You're on the list.");
    } catch {
      toast.error('Something went wrong. Try again.');
    } finally {
      setNotifying(false);
    }
  };

  const feeBars = [
    { label: 'Other platforms', width: '85%', color: 'bg-red-200', pct: '12–15%' },
    { label: 'Other platforms', width: '55%', color: 'bg-orange-200', pct: '8–10%' },
    { label: 'The Honey Groove', width: '40%', color: 'bg-green-200', pct: '6%', amber: true },
  ];

  const comingItems = [
    'Buy Now, Make Offer, and Trade listing types',
    'Mutual Hold protection for every trade',
    'Dream List matching — get alerted instantly',
    'Seller profiles with verified ratings',
    'Express checkout with Stripe',
    'Gold member early access',
  ];

  return (
    <div className="max-w-[680px] mx-auto px-4 py-6 pb-24" data-testid="honeypot-teaser">

      {/* Disabled tabs — mirror ISOPage tab structure */}
      <Tabs value="shop" className="mb-6">
        <TabsList className="grid grid-cols-3 w-full">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="shop"
                  className="pointer-events-none opacity-40"
                  data-testid="teaser-tab-shop"
                >
                  Shop
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent>Shop opens soon. Tap Notify Me below.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="sell"
                  className="pointer-events-none opacity-40"
                  data-testid="teaser-tab-sell"
                >
                  Sell
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent>Listings open when the Honeypot launches.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <TabsTrigger
                  value="seek"
                  className="pointer-events-none opacity-40"
                  data-testid="teaser-tab-seek"
                >
                  Seek
                </TabsTrigger>
              </TooltipTrigger>
              <TooltipContent>Post your wants when the market opens.</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </TabsList>
      </Tabs>

      {/* Hero */}
      <div className="text-center py-10 bg-[#FFF8EE] rounded-2xl border border-[#F5E6CC] mb-6 px-6">
        <div className="inline-flex items-center justify-center mb-4">
          <svg
            width="64"
            height="64"
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ filter: 'drop-shadow(0 0 8px rgba(218,165,32,0.5))' }}
            className="animate-[pulse_2.5s_ease-in-out_infinite]"
            data-testid="teaser-honeypot-icon"
          >
            <ellipse cx="32" cy="44" rx="18" ry="14" fill="#DAA520" opacity="0.15" />
            <path
              d="M22 20 C22 14 28 10 32 10 C36 10 42 14 42 20 L44 42 C44 48 38 54 32 54 C26 54 20 48 20 42 Z"
              fill="#DAA520"
              opacity="0.9"
            />
            <ellipse cx="32" cy="20" rx="10" ry="6" fill="#C8861A" opacity="0.7" />
            <path d="M28 28 Q32 32 36 28" stroke="#FFF8EE" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            <path d="M29 35 Q32 38 35 35" stroke="#FFF8EE" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          </svg>
        </div>
        <h1
          className="text-[28px] md:text-[32px] font-bold text-[#2A1A06] mb-3 leading-tight"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          data-testid="teaser-headline"
        >
          The Honeypot is almost ready.
        </h1>
        <p className="text-[15px] text-[#8A6B4A] max-w-md mx-auto" style={{ fontFamily: 'Georgia, serif' }}>
          A marketplace built for vinyl collectors. Buy, sell, and trade records with the lowest fees in the game — and protection built into every trade.
        </p>
      </div>

      {/* Feature pillars */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {[
          { icon: ShoppingBag, title: 'Shop', body: 'Browse records listed by collectors in the hive.' },
          { icon: ArrowRightLeft, title: 'Trade', body: 'Swap records with Mutual Hold protection on every deal.' },
          { icon: Search, title: 'Seek', body: 'Post what you\'re hunting and get matched instantly.' },
        ].map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="bg-white border border-[#F5E6CC] rounded-xl p-6 shadow-sm"
            data-testid={`teaser-pillar-${title.toLowerCase()}`}
          >
            <Icon className="w-6 h-6 text-[#C8861A] mb-3" />
            <p className="font-bold text-[#2A1A06] mb-1">{title}</p>
            <p className="text-sm text-[#8A6B4A]">{body}</p>
          </div>
        ))}
      </div>

      {/* Fee comparison */}
      <div className="bg-white border border-[#F5E6CC] rounded-xl p-6 mb-6">
        <h2 className="font-bold text-[#2A1A06] mb-4 text-base" style={{ fontFamily: "'Playfair Display', Georgia, serif" }}>
          Fees that actually make sense.
        </h2>
        <div className="space-y-3" data-testid="teaser-fee-bars">
          {feeBars.map(({ label, width, color, pct, amber }, i) => (
            <div key={i} className="flex items-center gap-3">
              <span
                className="text-sm w-40 shrink-0 truncate"
                style={amber ? { color: '#C8861A', fontWeight: 600 } : { color: '#8A6B4A' }}
              >
                {label}
              </span>
              <div className="flex-1 h-8 bg-stone-100 rounded-lg overflow-hidden">
                <div
                  className={`h-full ${color} rounded-lg`}
                  style={{
                    width,
                    transformOrigin: 'left',
                    transform: `scaleX(${animated ? 1 : 0})`,
                    transition: 'transform 0.5s ease-out',
                  }}
                />
              </div>
              <span className="text-sm font-medium text-[#2A1A06] w-12 text-right shrink-0">{pct}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-[#8A6B4A] mt-3 italic">Gold members pay just 4%.</p>
      </div>

      {/* Gold early access card */}
      <div
        className="border-2 border-[#DAA520] rounded-xl p-6 bg-gradient-to-br from-[#FFF9E6] to-[#FFF3E0] mb-6 hover:shadow-[0_0_20px_rgba(218,165,32,0.3)] transition-shadow"
        data-testid="teaser-gold-card"
      >
        <h2
          className="font-bold text-[#2A1A06] text-lg mb-1"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Get Gold early access.
        </h2>
        <p className="text-sm text-[#8A6B4A] mb-4">
          Gold members get in before everyone else and pay 4% fees — the lowest rate we offer.
        </p>
        <Button
          onClick={() => navigate('/gold')}
          className="rounded-full font-bold text-[#2A1A06]"
          style={{ background: '#E8A820' }}
          data-testid="teaser-gold-btn"
        >
          Get Gold
        </Button>
        <p className="text-xs text-[#8A6B4A] mt-2">$4.99/month. Cancel anytime.</p>
      </div>

      {/* Notify Me */}
      <div className="text-center mb-6" data-testid="teaser-notify-section">
        {user?.honeypot_notify_me ? (
          <Button
            disabled
            className="w-full sm:w-auto rounded-full font-bold text-white px-8"
            style={{ background: '#C8861A' }}
            data-testid="teaser-notify-confirmed"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            You're on the list.
          </Button>
        ) : (
          <Button
            onClick={handleNotify}
            disabled={notifying}
            variant="outline"
            className="w-full sm:w-auto rounded-full font-bold px-8 border-2"
            style={{ borderColor: '#C8861A', color: '#C8861A', background: 'transparent' }}
            data-testid="teaser-notify-btn"
          >
            <Bell className="w-4 h-4 mr-2" />
            {notifying ? 'Saving…' : 'Notify me when it opens'}
          </Button>
        )}
        {!user?.honeypot_notify_me && (
          <p className="text-xs text-[#8A6B4A] mt-2">We'll email you the moment the Honeypot goes live.</p>
        )}
      </div>

      {/* What's Coming */}
      <div className="bg-[#FFF8EE] border border-[#F5E6CC] rounded-xl p-6" data-testid="teaser-coming-list">
        <h2
          className="font-bold text-[#2A1A06] mb-4 text-base"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          What's coming.
        </h2>
        <ul className="space-y-2">
          {comingItems.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-[#2A1A06]">
              <CheckCircle2 className="w-4 h-4 text-[#C8861A] mt-0.5 shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default HoneypotTeaser;
