import { useCallback, useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';

/**
 * useShareCard — reusable hook for all share card types.
 *
 * Usage:
 *   const { cardRef, exporting, exportCard } = useShareCard({
 *     cardType: 'now_spinning',
 *     filename: 'thg-now-spinning',
 *     title: 'Check out what I'm spinning — The Honey Groove',
 *     userId: user?.id,
 *   });
 *   <NowSpinningCard ref={cardRef} ... />
 *   <button onClick={() => exportCard([coverUrl])}>Share</button>
 */
export function useShareCard({ cardType, filename = 'thg-share', title = 'The Honey Groove', userId } = {}) {
  const cardRef = useRef(null);
  const [exporting, setExporting] = useState(false);

  const preflightImage = (url) => new Promise((resolve) => {
    if (!url) { resolve(false); return; }
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = url;
  });

  // Wraps canvas.toBlob in a Promise so the full chain is properly awaited
  const canvasToBlob = (canvas) => new Promise((resolve) => {
    canvas.toBlob(resolve, 'image/png');
  });

  const exportCard = useCallback(async (imageUrls = []) => {
    if (!cardRef.current) {
      console.error('[ShareCard] exportCard called but cardRef.current is null — card not mounted?');
      return;
    }
    console.log('[ShareCard] exportCard START', { cardType, el: cardRef.current?.tagName, id: cardRef.current?.id });
    setExporting(true);

    try {
      // Pre-flight images into browser cache
      await Promise.all(imageUrls.filter(Boolean).map(preflightImage));

      // Card is always off-screen (position:fixed; left:-9999px) — no display toggle needed.
      // Just wait for fonts + images to settle before capture.
      await new Promise(r => setTimeout(r, 400));

      console.log('[ShareCard] calling html2canvas...');
      const canvas = await html2canvas(cardRef.current, {
        width: 1080,
        height: 1920,
        scale: 1,
        useCORS: true,
        allowTaint: false,
        backgroundColor: null,
        logging: false,
      });
      console.log('[ShareCard] html2canvas done, canvas:', canvas.width, 'x', canvas.height);

      // ─── PILL / BADGE OVERDRAW ──────────────────────────────────────────────
      // html2canvas's returned canvas may have an internal state that prevents
      // subsequent draws from appearing in toBlob. We blit it onto a fresh canvas
      // so our pill/badge draws are guaranteed to be included in the final PNG.
      // ────────────────────────────────────────────────────────────────────────
      const output = document.createElement('canvas');
      output.width = 1080;
      output.height = 1920;
      const ctx = output.getContext('2d');
      ctx.drawImage(canvas, 0, 0);
      console.log('[ShareCard] blitted html2canvas onto fresh output canvas');

      console.log('[ShareCard] DRAWING PILL: post-process start — scanning for [data-canvas-pill] elements');
      if (!ctx) {
        console.error('[ShareCard] DRAWING PILL: canvas.getContext(2d) returned null');
      } else {
        const cardRect = cardRef.current.getBoundingClientRect();
        console.log('[ShareCard] DRAWING PILL: cardRect =', JSON.stringify({ left: cardRect.left, top: cardRect.top, w: cardRect.width, h: cardRect.height }));

        // querySelectorAll on the live card DOM — pills are always mounted (off-screen)
        const pillEls = cardRef.current.querySelectorAll('[data-canvas-pill]');
        console.log('[ShareCard] DRAWING PILL: found', pillEls.length, 'element(s):', Array.from(pillEls).map(el => el.dataset.canvasPill));

        // Also check globally so we can tell if the elements exist at all vs. not being descendants
        const globalPills = document.querySelectorAll('[data-canvas-pill]');
        console.log('[ShareCard] DRAWING PILL: global [data-canvas-pill] count =', globalPills.length);

        // roundRect polyfill — required for Chrome <99, Safari <15.4
        const rrect = (c, x, y, w, h, r) => {
          if (typeof c.roundRect === 'function') { c.roundRect(x, y, w, h, r); return; }
          c.moveTo(x + r, y);
          c.lineTo(x + w - r, y);
          c.arcTo(x + w, y, x + w, y + r, r);
          c.lineTo(x + w, y + h - r);
          c.arcTo(x + w, y + h, x + w - r, y + h, r);
          c.lineTo(x + r, y + h);
          c.arcTo(x, y + h, x, y + h - r, r);
          c.lineTo(x, y + r);
          c.arcTo(x, y, x + r, y, r);
          c.closePath();
        };

        pillEls.forEach((el, idx) => {
          const r = el.getBoundingClientRect();
          const x = r.left - cardRect.left;
          const y = r.top - cardRect.top;
          const w = r.width;
          const h = r.height;
          const pillType = el.dataset.canvasPill;
          console.log(`[ShareCard] DRAWING PILL [${idx}] type="${pillType}" coords={x:${x.toFixed(1)}, y:${y.toFixed(1)}, w:${w.toFixed(1)}, h:${h.toFixed(1)}}`);

          ctx.save();
          try {
            if (pillType === 'daily-prompt') {
              console.log('DRAWING PILL — daily-prompt background start');
              ctx.fillStyle = '#F0E6D0';
              ctx.beginPath();
              rrect(ctx, x, y, w, h, h / 2);
              ctx.fill();
              ctx.strokeStyle = '#C4A96A';
              ctx.lineWidth = 2;
              ctx.stroke();
              console.log('DRAWING PILL — daily-prompt fillText');
              ctx.fillStyle = '#8B6914';
              ctx.font = 'bold 26px Arial, sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('🐝 DAILY PROMPT', x + w / 2, y + h / 2);
              console.log('DRAWING PILL — daily-prompt done');

            } else if (pillType === 'gold-member') {
              console.log('DRAWING PILL — gold-member background start');
              ctx.fillStyle = '#FFF3CD';
              ctx.beginPath();
              rrect(ctx, x, y, w, h, h / 2);
              ctx.fill();
              console.log('DRAWING PILL — gold-member fillText');
              ctx.fillStyle = '#000000';
              ctx.font = 'bold 22px Arial, sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('🏅 Gold Member', x + w / 2, y + h / 2);
              console.log('DRAWING PILL — gold-member done');

            } else if (pillType === 'verified') {
              console.log('DRAWING PILL — verified background start');
              ctx.fillStyle = '#E8F4FD';
              ctx.beginPath();
              rrect(ctx, x, y, w, h, h / 2);
              ctx.fill();
              ctx.strokeStyle = '#4A90D9';
              ctx.lineWidth = 2;
              ctx.stroke();
              console.log('DRAWING PILL — verified fillText');
              ctx.fillStyle = '#1A5276';
              ctx.font = 'bold 22px Arial, sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('✓ Verified', x + w / 2, y + h / 2);
              console.log('DRAWING PILL — verified done');

            } else {
              console.warn('[ShareCard] DRAWING PILL — unknown pillType:', pillType);
            }
          } catch (pillErr) {
            console.error('[ShareCard] DRAWING PILL — draw error for type:', pillType, pillErr);
          }
          ctx.restore();
        });
        console.log('[ShareCard] DRAWING PILL: post-process complete');
      }
      // ─── END PILL OVERDRAW ──────────────────────────────────────────────────

      const blob = await canvasToBlob(output);
      if (!blob) { setExporting(false); return; }

      trackEvent('share_card_generated', { card_type: cardType, user_id: userId });

      const fname = `${filename}-${Date.now()}.png`;
      const file = new File([blob], fname, { type: 'image/png' });

      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        try {
          await navigator.share({ files: [file], title });
          trackEvent('share_card_shared', { card_type: cardType, share_method: 'native_share', user_id: userId });
        } catch (err) {
          if (err?.name === 'AbortError') {
            // User dismissed the share sheet — no action needed
          } else {
            // iOS gesture timeout or other error — open image directly so user can save
            openImageFallback(blob, fname, cardType, userId);
          }
        }
      } else {
        downloadBlob(blob, fname, cardType, userId);
      }
    } catch (e) {
      console.error('[ShareCard] exportCard FAILED:', e);
      toast.error('Could not generate share card. Try again.');
    } finally {
      setExporting(false);
    }
  }, [cardType, filename, title, userId]); // eslint-disable-line react-hooks/exhaustive-deps

  return { cardRef, exporting, exportCard };
}

function downloadBlob(blob, fname, cardType, userId) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fname;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 10000);
  trackEvent('share_card_downloaded', { card_type: cardType, user_id: userId });
}

// iOS fallback: open the image as a blob URL in the current tab.
// Safari shows the PNG full-screen and the user can tap Share → Save Image
// or share directly to Instagram Stories.
function openImageFallback(blob, fname, cardType, userId) {
  const url = URL.createObjectURL(blob);
  // Try opening in a new tab first; if blocked, navigate current tab
  const w = window.open(url, '_blank');
  if (!w) {
    // Popup blocked — navigate current tab to the image
    const a = document.createElement('a');
    a.href = url;
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
  trackEvent('share_card_downloaded', { card_type: cardType, share_method: 'image_fallback', user_id: userId });
}
