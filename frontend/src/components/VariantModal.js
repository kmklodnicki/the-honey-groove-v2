import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import { X, ExternalLink, Users, Search, Heart, BarChart3, DollarSign, TrendingUp, TrendingDown, Loader2, Calendar, Tag, Disc, MapPin } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { RarityCard } from './RarityBadge';
import VariantCompletion from './VariantCompletion';
import VariantActions from './VariantActions';
import AlbumArt from './AlbumArt';
import { useVariantModal } from '../context/VariantModalContext';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

function slugify(text) {
  return (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

const StatMini = ({ icon: Icon, label, value }) => (
  <div className="text-center">
    <div className="flex items-center justify-center gap-1 mb-0.5">
      <Icon className="w-3.5 h-3.5 text-honey-amber" />
    </div>
    <p className="text-lg font-heading font-bold text-vinyl-black">{value ?? '—'}</p>
    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
  </div>
);

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
      .catch(() => {
        // Try fetching by discogs_id from a different variant slug
        if (discogs_id) {
          // Fallback: just show what we have from modal props
          setData(null);
        }
      })
      .finally(() => setLoading(false));
  }, [modal]);

  if (!modal) return null;

  const { artist, album, variant } = modal;
  const ov = data?.variant_overview;
  const dm = data?.demand;
  const val = data?.value;
  const rarity = data?.rarity;
  const variantSlug = `/vinyl/${slugify(ov?.artist || artist)}/${slugify(ov?.album || album)}/${slugify(ov?.variant || variant) || 'standard'}`;

  return (
    <Dialog open={!!modal} onOpenChange={(open) => { if (!open) closeVariantModal(); }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] p-0 overflow-hidden rounded-2xl [&>button:last-child]:hidden" aria-describedby="variant-modal-desc">
        <DialogTitle className="sr-only">{ov?.artist || artist} — {ov?.album || album}</DialogTitle>
        <span id="variant-modal-desc" className="sr-only">Variant details for {ov?.variant || variant}</span>

        <div className="overflow-y-auto max-h-[85vh]" data-testid="variant-modal">
          {/* Album art with variant label */}
          <div className="relative aspect-square w-full bg-vinyl-black">
            <AlbumArt
              src={ov?.cover_url || modal.cover_url}
              alt={`${ov?.artist || artist} ${ov?.album || album} ${ov?.variant || variant} vinyl record`}
              className="w-full h-full object-cover"
            />
            {/* Variant label overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent p-4 pt-12">
              <p className="text-white text-lg font-heading font-bold leading-tight drop-shadow-md">
                {ov?.album || album}
              </p>
              <p className="text-white/80 text-sm mt-0.5 drop-shadow-md">
                {ov?.artist || artist}
              </p>
              <span className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white border border-white/20" data-testid="variant-label-overlay">
                {ov?.variant || variant || 'Standard Black Vinyl'}
              </span>
            </div>
            {/* Close button */}
            <button
              onClick={closeVariantModal}
              className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/60 transition-colors"
              data-testid="variant-modal-close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {loading && (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-honey-amber" />
              </div>
            )}

            {!loading && data && (
              <>
                {/* Metadata badges */}
                <div className="flex flex-wrap gap-1.5">
                  {ov?.year && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 text-xs text-stone-600">
                      <Calendar className="w-3 h-3" /> {ov.year}
                    </span>
                  )}
                  {ov?.format && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 text-xs text-stone-600">
                      <Disc className="w-3 h-3" /> {ov.format}
                    </span>
                  )}
                  {ov?.label && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 text-xs text-stone-600">
                      <Tag className="w-3 h-3" /> {ov.label}
                    </span>
                  )}
                  {ov?.pressing_country && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 text-xs text-stone-600">
                      <MapPin className="w-3 h-3" /> {ov.pressing_country}
                    </span>
                  )}
                </div>

                {/* Stats row */}
                {dm && (
                  <div className="grid grid-cols-3 gap-2">
                    <StatMini icon={Users} label="Collectors" value={dm.owners_count} />
                    <StatMini icon={Search} label="Searching" value={dm.iso_count} />
                    <StatMini icon={Heart} label="Posts" value={dm.post_count} />
                  </div>
                )}

                {/* Action buttons */}
                {ov && <VariantActions variant={ov} />}

                {/* Rarity */}
                {rarity && <RarityCard rarity={rarity} />}

                {/* Market Value */}
                {val && (val.recent_sales_count > 0 || val.discogs_median) && (
                  <Card className="p-4 border-honey/20">
                    <p className="text-xs font-bold text-vinyl-black/50 uppercase tracking-wider mb-2">Market Value</p>
                    {val.recent_sales_count > 0 ? (
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                          <p className="text-lg font-heading font-bold">${val.average_value?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">Avg</p>
                        </div>
                        <div>
                          <p className="text-lg font-heading font-bold">${val.highest_sale?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">High</p>
                        </div>
                        <div>
                          <p className="text-lg font-heading font-bold">${val.lowest_sale?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">Low</p>
                        </div>
                      </div>
                    ) : val.discogs_median ? (
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                          <p className="text-lg font-heading font-bold">${val.discogs_median?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">Median</p>
                        </div>
                        <div>
                          <p className="text-lg font-heading font-bold">${val.discogs_high?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">High</p>
                        </div>
                        <div>
                          <p className="text-lg font-heading font-bold">${val.discogs_low?.toFixed(2)}</p>
                          <p className="text-[10px] text-muted-foreground">Low</p>
                        </div>
                      </div>
                    ) : null}
                  </Card>
                )}

                {/* Variant Completion */}
                {ov?.discogs_id && <VariantCompletion discogsId={ov.discogs_id} />}

                {/* View Full Page link */}
                <Button
                  onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                  variant="outline"
                  className="w-full rounded-full border-honey/30 text-sm hover:bg-honey/10"
                  data-testid="variant-modal-fullpage"
                >
                  View Full Variant Page <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                </Button>
              </>
            )}

            {!loading && !data && (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground">Variant data unavailable</p>
                <Button
                  onClick={() => { closeVariantModal(); navigate(variantSlug); }}
                  className="mt-3 rounded-full bg-honey text-vinyl-black hover:bg-honey-amber text-sm"
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
