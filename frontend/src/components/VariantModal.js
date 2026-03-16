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
    const { artist, album, variant, discogs_id } = modal;
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

  // Combined stats for the unified grid
  const hasMarket = val && (val.recent_sales_count > 0 || val.discogs_median);
  const medianPrice = val?.recent_sales_count > 0 ? val.average_value : val?.discogs_median;
  const highPrice = val?.recent_sales_count > 0 ? val.highest_sale : val?.discogs_high;

  return (
    <Dialog open={!!modal} onOpenChange={(open) => { if (!open) closeVariantModal(); }}>
      <DialogContent className="sm:max-w-[280px] max-w-[92vw] max-h-[85vh] p-0 overflow-hidden rounded-2xl [&>button:last-child]:hidden" aria-describedby="variant-modal-desc">
        <DialogTitle className="sr-only">{ov?.artist || artist} — {ov?.album || album}</DialogTitle>
        <span id="variant-modal-desc" className="sr-only">Variant details</span>

        <div className="overflow-y-auto max-h-[85vh]" data-testid="variant-modal">
          {/* Header — tight */}
          <div className="flex items-center gap-2 p-2 bg-vinyl-black relative">
            <div className="w-12 h-12 rounded-md overflow-hidden shrink-0 shadow-lg">
              <AlbumArt
                src={ov?.cover_url || modal.cover_url}
                alt={`${ov?.artist || artist} ${ov?.album || album}`}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1 min-w-0 pr-5">
              <p className="text-white text-[11px] font-heading font-bold leading-tight line-clamp-2">
                {ov?.album || album}
              </p>
              <p className="text-white/60 text-[9px] mt-px truncate">
                {ov?.artist || artist}
              </p>
              <span className="inline-block mt-0.5 px-1.5 py-px rounded-full text-[8px] font-semibold bg-white/20 backdrop-blur-sm text-white border border-white/20" data-testid="variant-label-overlay">
                {ov?.variant || variant || 'Standard Black Vinyl'}
              </span>
            </div>
            <button
              onClick={closeVariantModal}
              className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/60 transition-colors"
              data-testid="variant-modal-close"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-2 space-y-1.5">
            {loading && (
              <div className="flex justify-center py-3">
                <Loader2 className="w-4 h-4 animate-spin text-honey-amber" />
              </div>
            )}

            {!loading && data && (
              <>
                {/* Metadata pills — single row */}
                <div className="flex flex-wrap gap-px">
                  {ov?.year && (
                    <span className="inline-flex items-center gap-0.5 px-1 py-px rounded-full bg-stone-100 text-[8px] text-stone-500">
                      <Calendar className="w-2 h-2" /> {ov.year}
                    </span>
                  )}
                  {ov?.format && (
                    <span className="inline-flex items-center gap-0.5 px-1 py-px rounded-full bg-stone-100 text-[8px] text-stone-500">
                      <Disc className="w-2 h-2" /> {ov.format}
                    </span>
                  )}
                  {ov?.label && (
                    <span className="inline-flex items-center gap-0.5 px-1 py-px rounded-full bg-stone-100 text-[8px] text-stone-500">
                      <Tag className="w-2 h-2" /> {ov.label}
                    </span>
                  )}
                  {ov?.pressing_country && (
                    <span className="inline-flex items-center gap-0.5 px-1 py-px rounded-full bg-stone-100 text-[8px] text-stone-500">
                      <MapPin className="w-2 h-2" /> {ov.pressing_country}
                    </span>
                  )}
                </div>

                {/* Rarity pill — inline */}
                {rarity?.tier && (
                  <div className="flex items-center gap-1.5">
                    <RarityPill tier={rarity.tier} size="sm" />
                    {rarity.discogs_owners != null && (
                      <span className="text-[8px] text-stone-400">{rarity.discogs_owners.toLocaleString()} owners · {(rarity.discogs_wantlist || 0).toLocaleString()} want</span>
                    )}
                  </div>
                )}

                {/* UNIFIED 5-column grid: Collectors | Searching | Posts | Median | High */}
                {(dm || hasMarket) && (
                  <div className="grid grid-cols-5 gap-px text-center bg-stone-50 rounded-lg p-1" data-testid="variant-unified-stats">
                    {dm ? (
                      <>
                        <div className="py-0.5">
                          <Users className="w-2.5 h-2.5 text-honey-amber mx-auto" />
                          <p className="text-[10px] font-bold leading-tight">{dm.owners_count ?? '—'}</p>
                          <p className="text-[7px] text-muted-foreground uppercase">Own</p>
                        </div>
                        <div className="py-0.5">
                          <Search className="w-2.5 h-2.5 text-honey-amber mx-auto" />
                          <p className="text-[10px] font-bold leading-tight">{dm.iso_count ?? '—'}</p>
                          <p className="text-[7px] text-muted-foreground uppercase">ISO</p>
                        </div>
                        <div className="py-0.5">
                          <Heart className="w-2.5 h-2.5 text-honey-amber mx-auto" />
                          <p className="text-[10px] font-bold leading-tight">{dm.post_count ?? '—'}</p>
                          <p className="text-[7px] text-muted-foreground uppercase">Posts</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="py-0.5 col-span-3 flex items-center justify-center">
                          <span className="text-[8px] text-stone-400">No community data</span>
                        </div>
                      </>
                    )}
                    {hasMarket ? (
                      <>
                        <div className="py-0.5">
                          <DollarSign className="w-2.5 h-2.5 text-emerald-500 mx-auto" />
                          <p className="text-[10px] font-bold leading-tight">${medianPrice?.toFixed(0)}</p>
                          <p className="text-[7px] text-muted-foreground uppercase">Med</p>
                        </div>
                        <div className="py-0.5">
                          <TrendingUp className="w-2.5 h-2.5 text-red-400 mx-auto" />
                          <p className="text-[10px] font-bold leading-tight">${highPrice?.toFixed(0)}</p>
                          <p className="text-[7px] text-muted-foreground uppercase">High</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="py-0.5 col-span-2 flex items-center justify-center">
                          <span className="text-[8px] text-stone-400">No sales</span>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Action buttons — compact row */}
                {ov && <VariantActions variant={ov} compact />}

                {/* Variant Completion */}
                {ov?.discogs_id && <VariantCompletion discogsId={ov.discogs_id} />}

                {/* View Full Page link */}
                <Button
                  onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                  variant="outline"
                  className="w-full rounded-full border-honey/30 text-[10px] hover:bg-honey/10 h-6"
                  data-testid="variant-modal-fullpage"
                >
                  View Full Page <ExternalLink className="w-2 h-2 ml-1" />
                </Button>
              </>
            )}

            {!loading && !data && (
              <div className="text-center py-2">
                <p className="text-[10px] text-muted-foreground">Variant data unavailable</p>
                <Button
                  onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                  className="mt-1 rounded-full bg-honey text-vinyl-black hover:bg-honey-amber text-[10px] h-6"
                >
                  Open Variant Page
                </Button>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
