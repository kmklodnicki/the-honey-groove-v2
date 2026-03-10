import React, { useState, useEffect } from 'react';
import { Check, Circle, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from './ui/card';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const ProgressBar = ({ pct }) => (
  <div className="w-full h-3 bg-stone-200/60 rounded-full overflow-hidden" data-testid="completion-progress-bar">
    <div
      className="h-full rounded-full transition-all duration-700 ease-out"
      style={{
        width: `${pct}%`,
        background: pct === 100
          ? 'linear-gradient(90deg, #10b981, #059669)'
          : 'linear-gradient(90deg, #FFD700, #E8A820)',
      }}
    />
  </div>
);

const VariantRow = ({ variant }) => (
  <div
    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${variant.owned ? 'bg-emerald-50/80' : 'bg-stone-50/60 hover:bg-stone-100/60'}`}
    data-testid={`variant-row-${variant.name.toLowerCase().replace(/\s+/g, '-')}`}
  >
    {variant.owned ? (
      <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
        <Check className="w-3 h-3 text-white" strokeWidth={3} />
      </div>
    ) : (
      <div className="w-5 h-5 rounded border-2 border-stone-300 shrink-0" />
    )}
    <span className={`text-sm ${variant.owned ? 'font-medium text-emerald-800' : 'text-stone-500'}`}>
      {variant.name}
    </span>
    {variant.release_ids?.length > 1 && (
      <span className="text-[10px] text-muted-foreground ml-auto">
        {variant.release_ids.length} pressings
      </span>
    )}
  </div>
);

export default function VariantCompletion({ discogsId }) {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!discogsId) return;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    axios.get(`${API}/vinyl/completion/${discogsId}`, { headers })
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [discogsId, token]);

  if (loading || !data || data.error || data.total_variants <= 1) return null;

  const { total_variants, owned_count, completion_pct, variants } = data;
  const owned = variants.filter(v => v.owned);
  const missing = variants.filter(v => !v.owned);
  const previewCount = 6;
  const needsExpand = variants.length > previewCount;
  const displayVariants = expanded ? variants : variants.slice(0, previewCount);

  return (
    <Card className="p-5 border-honey/20" data-testid="variant-completion-card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading text-lg font-bold text-vinyl-black">Variant Tracker</h3>
        <span className="text-sm font-medium text-honey-amber" data-testid="completion-count">
          {owned_count} / {total_variants} variants
        </span>
      </div>

      <ProgressBar pct={completion_pct} />

      <p className="text-right text-xs text-muted-foreground mt-1.5 mb-4" data-testid="completion-pct">
        {completion_pct}% complete
      </p>

      {/* Owned Section */}
      {owned.length > 0 && (
        <div className="mb-3">
          <p className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-1.5">Owned</p>
          <div className="space-y-1">
            {owned.map(v => <VariantRow key={v.name} variant={v} />)}
          </div>
        </div>
      )}

      {/* Missing Section */}
      {missing.length > 0 && (
        <div>
          <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1.5">Missing</p>
          <div className="space-y-1">
            {(expanded ? missing : missing.slice(0, Math.max(0, previewCount - owned.length))).map(v => (
              <VariantRow key={v.name} variant={v} />
            ))}
          </div>
        </div>
      )}

      {/* Expand/Collapse */}
      {needsExpand && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 flex items-center justify-center gap-1 text-xs text-honey-amber hover:text-amber-600 transition-colors py-1.5"
          data-testid="completion-toggle"
        >
          {expanded ? (
            <>Show Less <ChevronUp className="w-3.5 h-3.5" /></>
          ) : (
            <>Show All {total_variants} Variants <ChevronDown className="w-3.5 h-3.5" /></>
          )}
        </button>
      )}
    </Card>
  );
}
