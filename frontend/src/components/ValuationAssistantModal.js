import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent, DialogTitle } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { DollarSign, Check, Loader2, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import AlbumArt from './AlbumArt';

const API = process.env.REACT_APP_BACKEND_URL;

const ValuationAssistantModal = ({ open, onClose, onValuesUpdated }) => {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [values, setValues] = useState({});
  const [saving, setSaving] = useState({});
  const [showInfo, setShowInfo] = useState(false);
  const [successItem, setSuccessItem] = useState(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setSuccessItem(null);
    axios.get(`${API}/api/valuation/pending-items`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { setItems(r.data); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, [open, token]);

  const handleSave = async (item, val) => {
    const num = parseFloat(val);
    if (!num || num <= 0) { toast.error('Enter a valid amount'); return; }
    setSaving(p => ({ ...p, [item.id]: true }));
    try {
      const res = await axios.put(`${API}/api/valuation/manual-value/${item.id}`, { value: num }, { headers: { Authorization: `Bearer ${token}` } });
      setSuccessItem(item.album);
      setTimeout(() => setSuccessItem(null), 3000);
      setItems(prev => prev.filter(i => i.id !== item.id));
      if (res.data?.dream_value) onValuesUpdated?.(res.data.dream_value);
    } catch {
      toast.error('Could not save value');
    }
    setSaving(p => ({ ...p, [item.id]: false }));
  };

  const acceptHiveValue = (item) => {
    if (item.hive_average) {
      setValues(p => ({ ...p, [item.id]: item.hive_average.toString() }));
      handleSave(item, item.hive_average);
    }
  };

  return (
    <Dialog open={open} onOpenChange={v => !v && onClose()}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto p-0" data-testid="valuation-assistant-modal">
        {/* Header */}
        <div className="px-5 pt-5 pb-3">
          <DialogTitle className="font-heading text-lg leading-tight">
            Help the Hive Value Your Grails
          </DialogTitle>
          <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
            Some of your rarest wax doesn't have official market data yet. By adding your estimate, you help build a stable price guide for every collector in the Hive.
          </p>
        </div>

        {/* Success banner */}
        {successItem && (
          <div className="mx-5 mb-2 px-3 py-2 rounded-lg border text-sm font-medium honey-fade-in" style={{ background: 'rgba(255,215,0,0.1)', borderColor: 'rgba(200,134,26,0.3)', color: '#7A5A1A' }} data-testid="valuation-success-banner">
            <Check className="inline w-3.5 h-3.5 mr-1.5 -mt-0.5" />
            Benchmark Set! Your estimate for <span className="font-semibold">{successItem}</span> is now helping other collectors value their grails.
          </div>
        )}

        {/* Content */}
        <div className="px-5 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#C8861A' }} />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-10">
              <Check className="w-10 h-10 mx-auto mb-3" style={{ color: '#C8861A' }} />
              <p className="text-sm font-semibold">All dream records are valued!</p>
              <p className="text-xs text-muted-foreground mt-1">Your Dream Value is fully calculated.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map(item => (
                <div key={item.id} className="rounded-xl border border-stone-200 bg-stone-50/50 overflow-hidden" data-testid={`pending-item-${item.id}`}>
                  <div className="flex items-center gap-3 p-3">
                    <div className="w-14 h-14 rounded-lg overflow-hidden shrink-0 bg-stone-200">
                      {item.cover_url ? (
                        <AlbumArt src={item.cover_url} alt={item.album} className="w-14 h-14 object-cover" />
                      ) : (
                        <div className="w-14 h-14 flex items-center justify-center text-stone-400 text-xs">N/A</div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">{item.album}</p>
                      <p className="text-xs text-muted-foreground truncate">{item.artist}</p>

                      {/* Hive Benchmark */}
                      {item.hive_average > 0 && (
                        <div className="mt-1.5 flex items-center gap-1.5" data-testid={`hive-benchmark-${item.id}`}>
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(255,215,0,0.15)', color: '#7A5A1A' }}>
                            Hive Average: ${item.hive_average.toFixed(2)}
                          </span>
                          <span className="text-[10px] text-stone-400">
                            Based on {item.hive_count} {item.hive_count === 1 ? 'submission' : 'submissions'}.
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Value input area */}
                  <div className="px-3 pb-3 flex items-center gap-2">
                    <span className="text-[11px] text-stone-500 font-medium shrink-0">Your Estimate:</span>
                    <div className="relative flex-1">
                      <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-400" />
                      <Input
                        type="number"
                        step="0.01"
                        min="0.01"
                        placeholder="0.00"
                        value={values[item.id] || ''}
                        onChange={e => setValues(p => ({ ...p, [item.id]: e.target.value }))}
                        className="h-9 pl-6 text-sm"
                        data-testid={`manual-value-input-${item.id}`}
                      />
                    </div>
                    {item.hive_average > 0 && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => acceptHiveValue(item)}
                        disabled={saving[item.id]}
                        className="h-9 px-2.5 text-[11px] font-semibold rounded-full shrink-0 border-amber-300 hover:bg-amber-50"
                        data-testid={`accept-hive-btn-${item.id}`}
                      >
                        Accept Hive
                      </Button>
                    )}
                    <Button
                      size="sm"
                      onClick={() => handleSave(item, values[item.id])}
                      disabled={saving[item.id] || !values[item.id]}
                      className="h-9 px-3 rounded-full font-semibold text-xs border-0 shrink-0"
                      style={{ background: '#FFD700', color: '#1A1A1A' }}
                      data-testid={`save-value-btn-${item.id}`}
                    >
                      {saving[item.id] ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save to Hive'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* How it works accordion */}
          <button
            onClick={() => setShowInfo(p => !p)}
            className="flex items-center gap-1.5 mt-4 text-xs text-stone-400 hover:text-stone-600 transition-colors"
            data-testid="how-it-works-toggle"
          >
            <Info className="w-3.5 h-3.5" />
            How is this calculated?
            {showInfo ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {showInfo && (
            <div className="mt-2 p-3 rounded-lg bg-stone-50 border border-stone-200 text-xs text-stone-500 leading-relaxed honey-fade-in" data-testid="how-it-works-content">
              <p className="font-semibold text-stone-700 mb-1">The Hive Pricing Standard</p>
              <p>
                To keep our data accurate and protect the Hive from "troll" pricing or extreme inflation, we use a <strong>Trimmed Mean</strong> calculation.
              </p>
              <p className="mt-1.5">
                We collect every estimate submitted by users and automatically discard the highest and lowest 10% of entries. By averaging only the middle 80%, we ensure that one or two outliers don't skew the value of your collection. Your voice counts, but the community keeps it balanced.
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ValuationAssistantModal;
