import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Dialog, DialogContent, DialogTitle } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Search, DollarSign, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import AlbumArt from './AlbumArt';

const API = process.env.REACT_APP_BACKEND_URL;

const ValuationAssistantModal = ({ open, onClose, onValuesUpdated }) => {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [values, setValues] = useState({});
  const [saving, setSaving] = useState({});

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    axios.get(`${API}/api/valuation/pending-items`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { setItems(r.data); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, [open, token]);

  const handleSave = async (item) => {
    const val = parseFloat(values[item.id]);
    if (!val || val <= 0) { toast.error('Enter a valid amount'); return; }
    setSaving(p => ({ ...p, [item.id]: true }));
    try {
      const res = await axios.put(`${API}/api/valuation/manual-value/${item.id}`, { value: val }, { headers: { Authorization: `Bearer ${token}` } });
      setItems(prev => prev.filter(i => i.id !== item.id));
      toast.success(`Valued ${item.album} at $${val.toFixed(2)}`);
      if (res.data?.dream_value) onValuesUpdated?.(res.data.dream_value);
    } catch {
      toast.error('Could not save value');
    }
    setSaving(p => ({ ...p, [item.id]: false }));
  };

  return (
    <Dialog open={open} onOpenChange={v => !v && onClose()}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto" data-testid="valuation-assistant-modal">
        <DialogTitle className="font-heading text-lg">
          <Search className="inline w-4 h-4 mr-2 -mt-0.5" style={{ color: '#C8861A' }} />
          Valuation Assistant
        </DialogTitle>
        <p className="text-sm text-muted-foreground -mt-1 mb-3">
          We couldn't find market data for {items.length} of your grails yet. Manually add value now?
        </p>

        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#C8861A' }} />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-8">
            <Check className="w-8 h-8 mx-auto mb-2" style={{ color: '#C8861A' }} />
            <p className="text-sm font-medium">All dream records are valued!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <div key={item.id} className="flex items-center gap-3 p-3 rounded-xl border border-stone-200 bg-stone-50/50" data-testid={`pending-item-${item.id}`}>
                <div className="w-12 h-12 rounded-lg overflow-hidden shrink-0 bg-stone-200">
                  {item.cover_url ? (
                    <AlbumArt src={item.cover_url} alt={item.album} className="w-12 h-12 object-cover" />
                  ) : (
                    <div className="w-12 h-12 flex items-center justify-center text-stone-400 text-xs">N/A</div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.album}</p>
                  <p className="text-xs text-muted-foreground truncate">{item.artist}</p>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <div className="relative">
                    <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-400" />
                    <Input
                      type="number"
                      step="0.01"
                      min="0.01"
                      placeholder="0.00"
                      value={values[item.id] || ''}
                      onChange={e => setValues(p => ({ ...p, [item.id]: e.target.value }))}
                      className="w-24 h-9 pl-6 text-sm"
                      data-testid={`manual-value-input-${item.id}`}
                    />
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleSave(item)}
                    disabled={saving[item.id]}
                    className="h-9 px-3 rounded-full font-semibold text-xs border-0"
                    style={{ background: '#FFD700', color: '#1A1A1A' }}
                    data-testid={`save-value-btn-${item.id}`}
                  >
                    {saving[item.id] ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ValuationAssistantModal;
