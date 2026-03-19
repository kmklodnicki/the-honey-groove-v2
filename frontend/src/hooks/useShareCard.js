import { useCallback, useRef, useState } from 'react';
import html2canvas from 'html2canvas';
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

  const exportCard = useCallback(async (imageUrls = []) => {
    if (!cardRef.current) return;
    setExporting(true);
    try {
      // Pre-flight all images so they're in the browser cache before canvas capture
      await Promise.all(imageUrls.filter(Boolean).map(preflightImage));

      cardRef.current.style.display = 'flex';
      cardRef.current.style.position = 'fixed';
      cardRef.current.style.left = '-9999px';
      cardRef.current.style.top = '0';

      // Wait for fonts + images to settle
      await new Promise(r => setTimeout(r, 500));

      const canvas = await html2canvas(cardRef.current, {
        width: 1080,
        height: 1920,
        scale: 1,
        useCORS: true,
        allowTaint: false,
        backgroundColor: null,
        logging: false,
      });

      cardRef.current.style.display = 'none';

      trackEvent('share_card_generated', { card_type: cardType, user_id: userId });

      canvas.toBlob(async (blob) => {
        if (!blob) { setExporting(false); return; }
        const fname = `${filename}-${Date.now()}.png`;
        const file = new File([blob], fname, { type: 'image/png' });

        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          try {
            await navigator.share({ files: [file], title });
            trackEvent('share_card_shared', { card_type: cardType, share_method: 'native_share', user_id: userId });
          } catch {
            // User cancelled — don't track
          }
        } else {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = fname;
          a.click();
          URL.revokeObjectURL(url);
          trackEvent('share_card_downloaded', { card_type: cardType, user_id: userId });
        }
        setExporting(false);
      }, 'image/png');
    } catch {
      setExporting(false);
      if (cardRef.current) cardRef.current.style.display = 'none';
    }
  }, [cardType, filename, title, userId]);

  return { cardRef, exporting, exportCard };
}
