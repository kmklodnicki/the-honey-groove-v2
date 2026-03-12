import React from 'react';
import { AlertTriangle } from 'lucide-react';

/**
 * PHASE 1: Legal Shield — Public Disclosure footer for unofficial releases.
 * Renders the compliance disclaimer on every unofficial item page.
 */
const UnofficialDisclaimer = () => (
  <div
    className="mt-6 px-4 py-3 rounded-xl text-xs leading-relaxed"
    style={{
      background: 'rgba(74,74,74,0.06)',
      border: '1px solid rgba(74,74,74,0.12)',
      color: '#6B6B6B',
    }}
    data-testid="unofficial-disclaimer"
  >
    <div className="flex items-start gap-2">
      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-stone-400" />
      <p>
        <span className="font-semibold text-stone-500">NOTICE:</span> This release is identified as
        &lsquo;Unofficial.&rsquo; The Honey Groove facilitates the secondary market trade of these items for
        archival and collection purposes. The platform does not claim affiliation with the original
        rights holders or guarantee audio fidelity.
      </p>
    </div>
  </div>
);

export default UnofficialDisclaimer;
