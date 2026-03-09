import React from 'react';
import { ExternalLink, Award } from 'lucide-react';
import { Button } from '../components/ui/button';
import { usePageTitle } from '../hooks/usePageTitle';

const HONEY_SHOP_ITEMS = [
  {
    id: 'shield',
    honeyLabel: 'The Shield',
    name: 'Outer Sleeves (4mil Clarity)',
    descriptor: 'Crystal-clear outer protection for the records worth showing off.',
    url: 'https://amzn.to/4cxAUEJ',
    image: 'https://static.prod-images.emergentagent.com/jobs/088a9581-bbfd-42c2-ad31-f5535df4814c/images/003cc18cbe94235b06ae5e84c4d7555d2aafff5fecbdd0fc19177ae3512849a1.png',
  },
  {
    id: 'vault',
    honeyLabel: 'The Vault',
    name: 'Inner Sleeves (Antistatic Rice Paper)',
    descriptor: 'Antistatic inner sleeves that keep your vinyl clean and properly tucked away.',
    url: 'https://amzn.to/3MR1RJ9',
    image: 'https://static.prod-images.emergentagent.com/jobs/088a9581-bbfd-42c2-ad31-f5535df4814c/images/270f1ef0c78249dc2bef20519291dad14dbc31bba66c64257a0f509c69aa525c.png',
  },
  {
    id: 'polish',
    honeyLabel: 'The Polish',
    name: 'Complete Cleaning Kit',
    descriptor: 'A complete care kit for records that deserve a little extra love.',
    url: 'https://amzn.to/4unqpdG',
    image: 'https://static.prod-images.emergentagent.com/jobs/088a9581-bbfd-42c2-ad31-f5535df4814c/images/a9719d18d2e4b5ff6646469f8208dcd7bcaf089424a7f5a579593116d2db9308.png',
  },
];

const ApprovedSeal = () => (
  <div className="inline-flex items-center gap-1.5 bg-gradient-to-r from-amber-100/80 to-yellow-50/80 border border-amber-300/40 rounded-full px-3 py-1" data-testid="approved-seal">
    <Award className="w-3.5 h-3.5 text-amber-600" />
    <span className="text-[11px] font-semibold tracking-wide text-amber-700 uppercase">Honey Groove Approved</span>
  </div>
);

const ProductCard = ({ item }) => (
  <div
    className="group bg-white rounded-2xl border border-stone-200/60 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden flex flex-col"
    data-testid={`product-card-${item.id}`}
  >
    {/* Image */}
    <div className="relative aspect-square bg-stone-50 overflow-hidden">
      <img
        src={item.image}
        alt={`${item.name} - Vinyl Record Accessory`}
        className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
        loading="lazy"
      />
    </div>

    {/* Content */}
    <div className="flex flex-col flex-1 p-5 sm:p-6 gap-3">
      <ApprovedSeal />

      <div className="space-y-1">
        <p className="text-xs font-semibold tracking-widest uppercase text-amber-600" data-testid="honey-label">
          {item.honeyLabel}
        </p>
        <h3 className="font-heading text-lg text-stone-900 leading-snug" data-testid="product-name">
          {item.name}
        </h3>
      </div>

      <p className="text-sm text-stone-500 leading-relaxed flex-1" data-testid="product-descriptor">
        {item.descriptor}
      </p>

      <Button
        asChild
        className="mt-auto bg-stone-900 text-white hover:bg-stone-800 rounded-full gap-2 w-full"
        data-testid={`cta-${item.id}`}
      >
        <a href={item.url} target="_blank" rel="noopener noreferrer">
          View on Amazon
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </Button>
    </div>
  </div>
);

const EssentialsPage = () => {
  usePageTitle('Honey Shop');

  return (
    <div className="min-h-[calc(100vh-80px)] bg-[#FDFAF5]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16">
        {/* Header */}
        <div className="text-center mb-10 sm:mb-14 space-y-3" data-testid="essentials-header">
          <h1 className="font-heading text-4xl sm:text-5xl text-stone-900 tracking-tight">
            Honey Shop
          </h1>
          <p className="text-base text-stone-500 max-w-md mx-auto">
            The curated essentials that keep your collection sweet.
          </p>
          <p className="text-sm text-stone-400 italic">
            Preserve the pressings. Protect the hive.
          </p>
        </div>

        {/* Product Grid */}
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8"
          data-testid="product-grid"
        >
          {HONEY_SHOP_ITEMS.map(item => (
            <ProductCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default EssentialsPage;
