/**
 * Extracted sub-components from ISOPage.js for maintainability.
 * ISOCard, CommunityISOCard, ActiveTradeCard, ListingCard
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from '../ui/tooltip';
import { CheckCircle2, Trash2, DollarSign, Disc, ArrowRightLeft, MessageSquare, Shield, X, Zap } from 'lucide-react';
import AlbumArt from '../AlbumArt';
import { GradeLabel } from '../GradeLabel';
import { TitleBadge } from '../TitleBadge';
import { TagPill } from '../PostCards';
import { countryFlag } from '../../utils/countryFlag';
import UnofficialPill from '../UnofficialPill';

export const STATUS_CONFIG = {
  PROPOSED: { label: 'Proposed', color: 'bg-amber-100 text-amber-700' },
  COUNTERED: { label: 'Countered', color: 'bg-blue-100 text-blue-700' },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700' },
  DECLINED: { label: 'Declined', color: 'bg-red-100 text-red-700' },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-100 text-gray-600' },
  HOLD_PENDING: { label: 'Hold Pending', color: 'bg-amber-100 text-amber-700' },
  SHIPPING: { label: 'Shipping', color: 'bg-[#E8A820]/15 text-[#C8861A] border border-[#C8861A]/30' },
  CONFIRMING: { label: 'Confirming', color: 'bg-cyan-100 text-cyan-700' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  DISPUTED: { label: 'Disputed', color: 'bg-red-100 text-red-700' },
};

export const ISOCard = ({ iso, isOwn, onMarkFound, onDelete, onSetPriceAlert, onDemote }) => {
  const [alertInput, setAlertInput] = useState('');
  const [showAlertInput, setShowAlertInput] = useState(false);

  return (
    <Card className={`p-4 border-honey/30 transition-all ${iso.status === 'FOUND' ? 'opacity-60 bg-amber-50/30' : 'hover:shadow-md'}`} data-testid={`iso-item-${iso.id}`}>
      <div className="flex items-start gap-3">
        <div className="relative shrink-0">
          <AlbumArt src={iso.cover_url} alt={`${iso.artist} ${iso.album}${iso.pressing_notes ? ` ${iso.pressing_notes}` : ''} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" isUnofficial={iso.is_unofficial} />
          {iso.status === 'OPEN' && (
            <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #DAA520, #E8A820)', boxShadow: '0 2px 6px rgba(218,165,32,0.5)' }} data-testid={`seeking-bolt-${iso.id}`}>
              <Zap className="w-3 h-3 text-white fill-white" />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-heading text-base truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{iso.album}</h4>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${iso.status === 'FOUND' ? 'bg-amber-100 text-[#C8861A]' : ''}`}
              style={iso.status === 'OPEN' ? { background: 'rgba(255,215,0,0.15)', color: '#C8861A', border: '1.5px solid #DAA520' } : {}}
            >{iso.status === 'OPEN' ? 'SEEKING' : iso.status}</span>
          </div>
          <p className="text-sm text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{iso.artist}{iso.year ? ` (${iso.year})` : ''}</p>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {(iso.tags || []).map(tag => <TagPill key={tag} tag={tag} />)}
          </div>
          <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
            {iso.pressing_notes && <span>Press: {iso.pressing_notes}</span>}
            {iso.condition_pref && <span>Cond: {iso.condition_pref}</span>}
            {(iso.target_price_min || iso.target_price_max) && <span>Budget: {iso.target_price_min ? `$${iso.target_price_min}` : ''}{iso.target_price_min && iso.target_price_max ? ' – ' : ''}{iso.target_price_max ? (iso.target_price_min ? `$${iso.target_price_max}` : `up to $${iso.target_price_max}`) : ''}</span>}
          </div>
          {isOwn && iso.status === 'OPEN' && (
            <div className="mt-2">
              {iso.price_alert ? (
                <span className="inline-flex items-center gap-1 text-xs text-honey-amber bg-honey/10 px-2 py-0.5 rounded-full" data-testid={`price-alert-badge-${iso.id}`}>
                  <DollarSign className="w-3 h-3" /> Alert at ${iso.price_alert}
                  <button onClick={() => onSetPriceAlert(iso.id, null)} className="ml-1 text-muted-foreground hover:text-red-500"><X className="w-3 h-3" /></button>
                </span>
              ) : showAlertInput ? (
                <div className="flex items-center gap-1.5">
                  <Input type="number" placeholder="Target $" value={alertInput} onChange={e => setAlertInput(e.target.value)}
                    className="h-7 w-24 text-xs border-honey/50" data-testid={`price-alert-input-${iso.id}`} autoFocus />
                  <Button size="sm" className="h-7 px-2 text-xs bg-honey text-vinyl-black hover:bg-honey-amber rounded-full"
                    onClick={() => { if (alertInput) { onSetPriceAlert(iso.id, parseFloat(alertInput)); setShowAlertInput(false); setAlertInput(''); }}}
                    data-testid={`price-alert-save-${iso.id}`}>Set</Button>
                  <button onClick={() => setShowAlertInput(false)} className="text-xs text-muted-foreground hover:text-red-500">Cancel</button>
                </div>
              ) : (
                <button onClick={() => setShowAlertInput(true)}
                  className="text-[11px] text-muted-foreground hover:text-honey-amber transition-colors flex items-center gap-1"
                  data-testid={`set-price-alert-${iso.id}`}>
                  <DollarSign className="w-3 h-3" /> Set price alert
                </button>
              )}
            </div>
          )}
        </div>
        {isOwn && iso.status === 'OPEN' && (
          <div className="flex flex-col gap-1 shrink-0 items-end">
            <div className="flex gap-1">
              <Button size="sm" variant="ghost" className="text-[#C8861A] hover:bg-amber-50 h-8 px-2" onClick={() => onMarkFound(iso.id)} data-testid={`mark-found-${iso.id}`}><CheckCircle2 className="w-4 h-4" /></Button>
              <Button size="sm" variant="ghost" className="text-[#8A6B4A]/60 hover:bg-[#8A6B4A]/10 h-8 px-2" onClick={() => onDelete(iso.id)}><Trash2 className="w-4 h-4" /></Button>
            </div>
            {onDemote && (
              <button onClick={() => onDemote(iso.id)} className="text-[10px] text-[#C8861A]/70 hover:text-[#C8861A] transition-colors" data-testid={`demote-btn-${iso.id}`}>
                Back to Dreams
              </button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export const CommunityISOCard = ({ iso, onHaveThis }) => (
  <Card className="p-4 border-honey/30 hover:shadow-md transition-all" data-testid={`community-iso-${iso.id}`}>
    <div className="flex items-start gap-3">
      <AlbumArt src={iso.cover_url} alt={`${iso.artist} ${iso.album} vinyl record`} className="w-14 h-14 rounded-lg object-cover shadow" isUnofficial={iso.is_unofficial} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h4 className="font-heading text-base truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{iso.album}</h4>
          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-[#E8A820]/15 text-[#C8861A] border border-[#C8861A]/30">SEARCHING</span>
        </div>
        <p className="text-sm text-muted-foreground">{iso.artist}{iso.year ? ` (${iso.year})` : ''}</p>
        {iso.user && (
          <Link to={`/profile/${iso.user.username}`} className="text-xs text-honey-amber hover:underline">@{iso.user.username}</Link>
        )}
        <div className="flex flex-wrap gap-1.5 mt-1">
          {(iso.tags || []).map(tag => <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-honey/20 text-honey-amber font-medium">{tag}</span>)}
        </div>
        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
          {iso.pressing_notes && <span>Press: {iso.pressing_notes}</span>}
          {iso.condition_pref && <span>Cond: {iso.condition_pref}</span>}
          {(iso.target_price_min || iso.target_price_max) && <span>Budget: {iso.target_price_min ? `$${iso.target_price_min}` : ''}{iso.target_price_min && iso.target_price_max ? ' – ' : ''}{iso.target_price_max ? (iso.target_price_min ? `$${iso.target_price_max}` : `up to $${iso.target_price_max}`) : ''}</span>}
        </div>
      </div>
      <Button size="sm" className="bg-[#E8A820]/15 text-[#C8861A] hover:bg-[#E8A820]/25 rounded-full gap-1 shrink-0" onClick={() => onHaveThis(iso)} data-testid={`i-have-this-${iso.id}`}>
        <MessageSquare className="w-3 h-3" /> I have this
      </Button>
    </div>
  </Card>
);

export const ActiveTradeCard = ({ trade, currentUserId }) => {
  const isInitiator = trade.initiator_id === currentUserId;
  const otherUser = isInitiator ? trade.responder : trade.initiator;
  const sc = STATUS_CONFIG[trade.status] || STATUS_CONFIG.PROPOSED;
  return (
    <Link to="/trades" data-testid={`active-trade-${trade.id}`}>
      <Card className="p-4 border-honey/30 hover:shadow-md transition-all cursor-pointer">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <AlbumArt src={trade.offered_record?.cover_url} alt={`${trade.offered_record?.artist || ''} ${trade.offered_record?.title || 'Record'} vinyl record`} className="w-10 h-10 rounded object-cover" isUnofficial={trade.offered_record?.is_unofficial} />
            <div className="min-w-0">
              <p className="text-sm font-medium truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{trade.offered_record?.title || 'Your record'}</p>
              <p className="text-xs text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>with @{otherUser?.username || '?'}</p>
            </div>
          </div>
          <ArrowRightLeft className="w-4 h-4 text-honey shrink-0" />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="w-10 h-10 rounded bg-honey/20 flex items-center justify-center"><Disc className="w-4 h-4 text-honey" /></div>
            <p className="text-sm font-medium truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{trade.listing_record?.album || 'Their record'}</p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {trade.hold_enabled && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild><span data-testid="hold-shield-icon"><Shield className="w-3.5 h-3.5 text-honey-amber" /></span></TooltipTrigger>
                  <TooltipContent className="bg-vinyl-black text-white text-xs max-w-[200px]"><p>Mutual hold trade · both parties have skin in the game.</p></TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            <span className={`px-2 py-1 rounded-full text-xs font-bold ${sc.color}`}>{sc.label}</span>
          </div>
        </div>
      </Card>
    </Link>
  );
};

export const ListingCard = ({ listing, currentUserId, onProposeTrade, onBuyNow, onMakeOffer, onClick }) => {
  const typeConfig = {
    BUY_NOW: { label: 'Buy Now', color: 'bg-amber-100/60 text-[#C8861A]' },
    MAKE_OFFER: { label: 'Offer', color: 'bg-amber-100/60 text-[#C8861A]' },
    TRADE: { label: 'Trade', color: 'bg-[#E8A820]/15 text-[#C8861A] border border-[#C8861A]/30' },
  };
  const tc = typeConfig[listing.listing_type] || typeConfig.BUY_NOW;
  const mainImage = (listing.photo_urls?.length > 0) ? listing.photo_urls[0] : listing.cover_url;

  return (
    <div className="flex items-center gap-3 py-3 px-2 cursor-pointer hover:bg-honey/5 transition-all duration-200"
      onClick={onClick} data-testid={`listing-${listing.id}`}>
      <div className="w-16 h-16 rounded-[10px] overflow-hidden bg-honey/10 shrink-0">
        {mainImage ? <AlbumArt src={mainImage} alt={`${listing.artist} ${listing.album}${listing.pressing_notes ? ` ${listing.pressing_notes}` : ''} vinyl record`} className="w-full h-full" isUnofficial={listing.is_unofficial} />
          : <div className="w-full h-full flex items-center justify-center"><Disc className="w-6 h-6 text-honey" /></div>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-heading text-sm font-bold truncate leading-tight" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{listing.album}</p>
        <p className="text-xs text-muted-foreground truncate" style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'100%'}}>{listing.artist}{listing.year ? ` (${listing.year})` : ''}</p>
        <div className="flex items-center gap-1.5 mt-1 flex-wrap">
          {listing.condition && <GradeLabel condition={listing.condition} variant="compact" />}
          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${tc.color}`}>{tc.label}</span>
          {listing.international_shipping && <span className="text-[10px] text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded-full border border-blue-200" data-testid={`listing-intl-${listing.id}`}>Intl Shipping</span>}
          {listing.is_test_listing && <span className="text-[10px] font-bold text-red-700 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-300" data-testid={`listing-test-badge-${listing.id}`}>TEST</span>}
          {listing.is_unofficial && <UnofficialPill variant="inline" />}
        </div>
        {listing.user && (
          <div className="flex items-center gap-1 mt-0.5">
            <Link to={`/profile/${listing.user.username}`} onClick={e => e.stopPropagation()}
              className="text-[11px] text-muted-foreground hover:underline">@{listing.user.username}{listing.user.country && <span className="ml-0.5">{countryFlag(listing.user.country)}</span>}</Link>
            {listing.user.title_label && <TitleBadge label={listing.user.title_label} />}
            {listing.user.rating > 0 && <span className="text-[11px] text-muted-foreground">· {listing.user.rating.toFixed(1)} ★</span>}
          </div>
        )}
      </div>
      {listing.price && (
        <span className="font-heading text-base text-[#C8861A] font-bold shrink-0">${listing.price}</span>
      )}
    </div>
  );
};
