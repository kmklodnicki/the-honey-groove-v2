import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import { X, ExternalLink, Users, Search, Heart, DollarSign, Loader2, Calendar, Tag, Disc, MapPin, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from './ui/button';
import { RarityPill } from './RarityBadge';
import VariantCompletion from './VariantCompletion';
import VariantActions from './VariantActions';
import AlbumArt from './AlbumArt';
import { useVariantModal } from '../context/VariantModalContext';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

import { API_BASE } from '../utils/apiBase';
const API = `${API_BASE}/api`;

function slugify(text) {
  return (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

export default function VariantModal() {
  const { modal, closeVariantModal } = useVariantModal();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!modal) { setData(null); return; }
    setLoading(true);
    const { artist, album, variant } = modal;
    const slug_a = slugify(artist);
    const slug_al = slugify(album);
    const slug_v = slugify(variant) || 'standard';
    axios.get(`${API}/vinyl/${slug_a}/${slug_al}/${slug_v}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [modal]);

  if (!modal) return null;

  const { artist, album, variant } = modal;
  const ov = data?.variant_overview;
  const dm = data?.demand;
  const val = data?.value;
  const rarity = data?.rarity;
  const variantSlug = `/vinyl/${slugify(ov?.artist || artist)}/${slugify(ov?.album || album)}/${slugify(ov?.variant || variant) || 'standard'}`;

  const hasMarket = val && (val.recent_sales_count > 0 || val.discogs_median);
  const medianPrice = val?.recent_sales_count > 0 ? val.average_value : val?.discogs_median;
  const highPrice = val?.recent_sales_count > 0 ? val.highest_sale : val?.discogs_high;
  const lowPrice = val?.recent_sales_count > 0 ? val.lowest_sale : val?.discogs_low;

  return (
    <Dialog open={!!modal} onOpenChange={(open) => { if (!open) closeVariantModal(); }}>
      <DialogContent
        className="p-0 overflow-hidden rounded-2xl [&>button:last-child]:hidden"
        style={{ minWidth: '340px', maxWidth: 'min(420px, 95vw)' }}
        aria-describedby="variant-modal-desc"
        data-testid="variant-modal-container"
      >
        <DialogTitle className="sr-only">{ov?.artist || artist} — {ov?.album || album}</DialogTitle>
        <span id="variant-modal-desc" className="sr-only">Variant details</span>

        <div className="flex flex-col max-h-[85vh]" data-testid="variant-modal">
          {/* ── FIXED TOP: Header + Stats + Buttons ── */}
          <div className="shrink-0">
            {/* Header */}
            <div className="flex items-center gap-3 p-3 bg-vinyl-black relative">
              <div className="w-16 h-16 rounded-lg overflow-hidden shrink-0 shadow-lg">
                <AlbumArt
                  src={ov?.cover_url || modal.cover_url}
                  alt={`${ov?.artist || artist} ${ov?.album || album}`}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1 min-w-0 pr-6">
                <p className="text-white text-base font-heading font-semibold leading-snug line-clamp-2" data-testid="variant-modal-title">
                  {ov?.album || album}
                </p>
                <p className="text-white/70 text-sm mt-0.5 truncate" data-testid="variant-modal-artist">
                  {ov?.artist || artist}
                </p>
                <span
                  className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
                  style={{
                    background: 'rgba(255,215,0,0.2)',
                    backdropFilter: 'blur(12px)',
                    WebkitBackdropFilter: 'blur(12px)',
                    color: '#FFD700',
                    border: '1.5px solid rgba(218,165,32,0.5)',
                  }}
                  data-testid="variant-label-overlay"
                >
                  {ov?.variant || variant || 'Standard Black Vinyl'}
                </span>
              </div>
              <button
                onClick={closeVariantModal}
                className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/60 transition-colors"
                data-testid="variant-modal-close"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Body — stats & buttons */}
            <div className="px-3 pt-2.5 pb-1 space-y-2">
              {loading && (
                <div className="flex justify-center py-6">
                  <Loader2 className="w-5 h-5 animate-spin text-honey-amber" />
                </div>
              )}

              {!loading && data && (
                <>
                  {/* Metadata pills row */}
                  <div className="flex flex-wrap gap-1">
                    {ov?.year && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F3EBE0] text-[10px] text-[#3A4D63]">
                        <Calendar className="w-2.5 h-2.5" /> {ov.year}
                      </span>
                    )}
                    {ov?.format && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F3EBE0] text-[10px] text-[#3A4D63]">
                        <Disc className="w-2.5 h-2.5" /> {ov.format}
                      </span>
                    )}
                    {ov?.label && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F3EBE0] text-[10px] text-[#3A4D63]">
                        <Tag className="w-2.5 h-2.5" /> {ov.label}
                      </span>
                    )}
                    {ov?.pressing_country && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F3EBE0] text-[10px] text-[#3A4D63]">
                        <MapPin className="w-2.5 h-2.5" /> {ov.pressing_country}
                      </span>
                    )}
                    {rarity?.tier && <RarityPill tier={rarity.tier} size="sm" />}
                  </div>

                  {/* Row 1: Community — Own / ISO / Posts */}
                  {dm && (
                    <div className="flex items-center justify-between bg-[#FFFBF2] rounded-lg px-3 py-2" data-testid="variant-stats-community">
                      <div className="flex items-center gap-1.5">
                        <Users className="w-3 h-3 text-honey-amber" />
                        <span className="text-sm font-semibold">{dm.owners_count ?? '—'}</span>
                        <span className="text-[10px] text-muted-foreground">Own</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Search className="w-3 h-3 text-honey-amber" />
                        <span className="text-sm font-semibold">{dm.iso_count ?? '—'}</span>
                        <span className="text-[10px] text-muted-foreground">ISO</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Heart className="w-3 h-3 text-honey-amber" />
                        <span className="text-sm font-semibold">{dm.post_count ?? '—'}</span>
                        <span className="text-[10px] text-muted-foreground">Posts</span>
                      </div>
                    </div>
                  )}

                  {/* Row 2: Market — Med / High / Low */}
                  {hasMarket && (
                    <div className="flex items-center justify-between bg-[#FFFBF2] rounded-lg px-3 py-2" data-testid="variant-stats-market">
                      <div className="flex items-center gap-1.5">
                        <DollarSign className="w-3 h-3 text-emerald-500" />
                        <span className="text-sm font-semibold">${medianPrice?.toFixed(0)}</span>
                        <span className="text-[10px] text-muted-foreground">Med</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <TrendingUp className="w-3 h-3 text-red-400" />
                        <span className="text-sm font-semibold">${highPrice?.toFixed(0)}</span>
                        <span className="text-[10px] text-muted-foreground">High</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <TrendingDown className="w-3 h-3 text-blue-400" />
                        <span className="text-sm font-semibold">${lowPrice?.toFixed(0) ?? '—'}</span>
                        <span className="text-[10px] text-muted-foreground">Low</span>
                      </div>
                    </div>
                  )}

                  {/* Action buttons — proper touch targets */}
                  {ov && <VariantActions variant={ov} />}
                </>
              )}

              {!loading && !data && (
                <div className="text-center py-4">
                  <p className="text-sm text-muted-foreground">Variant data unavailable</p>
                  <Button
                    onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                    className="mt-2 rounded-full bg-honey text-vinyl-black hover:bg-honey-amber text-sm min-h-[40px] px-6"
                  >
                    Open Variant Page
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* ── SCROLLABLE BOTTOM: Variant Tracker + Link ── */}
          {!loading && data && (
            <div className="flex-1 overflow-y-auto min-h-0 px-3 pb-3 space-y-2">
              {/* Divider */}
              <div className="border-t border-[#E5DBC8] pt-2" />

              {/* Variant Completion tracker */}
              {ov?.discogs_id && <VariantCompletion discogsId={ov.discogs_id} />}

              {/* View Full Page link */}
              <Button
                onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                variant="outline"
                className="w-full rounded-full border-honey/30 text-xs hover:bg-honey/10 min-h-[36px]"
                data-testid="variant-modal-fullpage"
              >
                View Full Variant Page <ExternalLink className="w-3 h-3 ml-1.5" />
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
