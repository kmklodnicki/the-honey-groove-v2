import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Disc, ArrowLeft, Play, Sparkles, TrendingUp, Share2, Download, ChevronDown } from 'lucide-react';
import { Button } from '../components/ui/button';
import { resolveImageUrl } from '../utils/imageUrl';
import html2canvas from 'html2canvas';

import { API as API_BASE } from '../utils/apiBase';

// ─── Proxy wrapper: route external images through our CORS-safe proxy ───
const proxyImageUrl = (url) => {
  if (!url) return null;
  const resolved = resolveImageUrl(url);
  if (!resolved) return null;
  // Only proxy external URLs (discogs, etc.) — local files are already CORS-safe
  if (resolved.startsWith('data:') || resolved.includes('/api/files/serve/')) return resolved;
  // Spotify CDN must be served directly — never proxy or re-host (Spotify Developer Policy)
  if (resolved.includes('i.scdn.co') || resolved.includes('scdn.co')) return resolved;
  if (resolved.startsWith('http')) {
    return `${API_BASE}/image-proxy?url=${encodeURIComponent(resolved)}`;
  }
  return resolved;
};

// ─── Pre-flight: ensure an image is loaded in the browser cache before export ───
const preflightImage = (url) => new Promise((resolve) => {
  if (!url) { resolve(false); return; }
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => resolve(true);
  img.onerror = () => resolve(false);
  img.src = url;
  setTimeout(() => resolve(false), 8000);
});

// ─── Report image with proxy + fallback chain ───
const ReportImg = ({ src, fallbacks, alt, className, style }) => {
  const [currentSrc, setCurrentSrc] = React.useState(() => proxyImageUrl(src));
  const [fallbackIdx, setFallbackIdx] = React.useState(0);
  const [failed, setFailed] = React.useState(false);

  React.useEffect(() => {
    setCurrentSrc(proxyImageUrl(src));
    setFallbackIdx(0);
    setFailed(false);
  }, [src]);

  const handleError = () => {
    const fbs = fallbacks || [];
    if (fallbackIdx < fbs.length) {
      const nextUrl = proxyImageUrl(fbs[fallbackIdx]);
      if (nextUrl) {
        setCurrentSrc(nextUrl);
        setFallbackIdx(i => i + 1);
        return;
      }
    }
    setFailed(true);
  };

  if (!currentSrc || failed) {
    return <div className={className} style={{ ...style, background: '#FFB800', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Disc style={{ width: '30%', height: '30%', color: 'rgba(0,0,0,0.15)' }} /></div>;
  }
  return <img src={currentSrc} alt={alt || ''} className={className} style={style} crossOrigin="anonymous" decoding="sync" fetchpriority="high" loading="eager" onError={handleError} draggable={false} />;
};

// ─── Color utility: extract dominant hue from an image via canvas sampling ───
const extractDominantColor = (imgUrl) => new Promise((resolve) => {
  if (!imgUrl) { resolve('#D4A828'); return; }
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 10; canvas.height = 10;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, 10, 10);
      const { data } = ctx.getImageData(0, 0, 10, 10);
      let r = 0, g = 0, b = 0;
      for (let i = 0; i < data.length; i += 4) { r += data[i]; g += data[i + 1]; b += data[i + 2]; }
      const px = data.length / 4;
      resolve(`rgb(${Math.round(r / px)}, ${Math.round(g / px)}, ${Math.round(b / px)})`);
    } catch { resolve('#D4A828'); }
  };
  img.onerror = () => resolve('#D4A828');
  img.src = proxyImageUrl(imgUrl) || resolveImageUrl(imgUrl);
});

const darken = (color, factor = 0.3) => {
  const m = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (!m) return '#0A0A0A';
  return `rgb(${Math.round(m[1] * factor)}, ${Math.round(m[2] * factor)}, ${Math.round(m[3] * factor)})`;
};

// ─── Slide Components ───

const IntroSlide = ({ username, dominantColor, dateRange }) => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-intro">
    <p className="text-sm font-medium tracking-[0.3em] uppercase mb-1" style={{ color: dominantColor }}>
      THE HONEY GROOVE
    </p>
    <p className="text-[11px] tracking-[0.15em] uppercase mb-4" style={{ color: 'rgba(255,255,255,0.35)', fontVariant: 'small-caps' }} data-testid="report-date-range">
      {dateRange}
    </p>
    <h1 className="font-heading text-3xl sm:text-5xl font-black text-white leading-tight mb-2" data-testid="intro-title">
      {username ? `@${username}'s` : 'Your'}<br />Week in the Hive
    </h1>
    <ChevronDown className="w-5 h-5 text-[#3A4D63] mt-4 animate-bounce" />
  </div>
);

const HeroSlide = ({ record, fallbacks, spinCount, isTopSpin, dominantColor }) => {
  const recordFallbacks = fallbacks || [];
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-hero">
      <p className="text-xs font-medium tracking-[0.2em] uppercase mb-6" style={{ color: dominantColor }}>
        {isTopSpin ? 'Top Spin of the Week' : 'The Newest Gem'}
      </p>
      {record?.cover_url ? (
        <div className="relative w-56 h-56 sm:w-72 sm:h-72 rounded-2xl overflow-hidden shadow-2xl mb-6 ring-2"
          style={{ ringColor: dominantColor, animation: 'kenBurns 20s ease-in-out infinite alternate' }}>
          <ReportImg src={record.cover_url} fallbacks={recordFallbacks} alt={`${record.artist} - ${record.title}`} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="w-56 h-56 rounded-2xl flex items-center justify-center mb-6" style={{ background: `${dominantColor}20` }}>
          <Disc className="w-20 h-20" style={{ color: dominantColor, opacity: 0.3 }} />
        </div>
      )}
      <h2 className="text-2xl sm:text-4xl font-black text-white leading-tight" data-testid="hero-title">
        {record?.title || 'No Activity'}
      </h2>
      <p className="text-base text-[#7A8694] mt-1">{record?.artist}</p>
      {spinCount > 0 && (
        <div className="flex items-center gap-2 mt-4">
          <Play className="w-5 h-5" style={{ color: dominantColor }} />
          <span className="text-lg font-bold" style={{ color: dominantColor }}>
            {spinCount} spin{spinCount !== 1 ? 's' : ''} this week
          </span>
        </div>
      )}
    </div>
  );
};

const StatsSlide = ({ stats, dominantColor }) => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-stats">
    <p className="text-xs font-medium tracking-[0.2em] uppercase mb-6" style={{ color: dominantColor }}>
      The Numbers
    </p>
    <div className="grid grid-cols-3 gap-6 max-w-md w-full">
      <div>
        <p className="text-4xl sm:text-6xl font-black" style={{ color: dominantColor }}>{stats.weekSpins}</p>
        <p className="text-xs text-[#3A4D63] mt-1 tracking-[0.15em] uppercase">Spins</p>
      </div>
      <div>
        <p className="text-4xl sm:text-6xl font-black" style={{ color: dominantColor }}>{stats.weekAdds}</p>
        <p className="text-xs text-[#3A4D63] mt-1 tracking-[0.15em] uppercase">Added</p>
      </div>
      <div>
        <p className="text-4xl sm:text-6xl font-black text-white">${stats.totalValue?.toLocaleString() || '0'}</p>
        <p className="text-xs text-[#3A4D63] mt-1 tracking-[0.15em] uppercase">Value</p>
      </div>
    </div>
    {stats.valueGained > 0 && (
      <div className="mt-6 flex items-center gap-2">
        <TrendingUp className="w-5 h-5" style={{ color: '#4ADE80' }} />
        <span className="text-sm font-bold text-green-400">
          +${stats.valueGained.toLocaleString()} this week
        </span>
      </div>
    )}
  </div>
);

const MilestoneSlide = ({ totalRecords, dominantColor }) => {
  const milestones = [50, 100, 150, 200, 250, 300, 400, 500, 750, 1000];
  const next = milestones.find(m => m > totalRecords);
  const away = next ? next - totalRecords : null;
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-milestone">
      <Sparkles className="w-10 h-10 mb-6" style={{ color: dominantColor }} />
      <p className="text-xs font-medium tracking-[0.2em] uppercase mb-4" style={{ color: dominantColor }}>
        Collection Milestone
      </p>
      <p className="text-6xl sm:text-8xl font-black text-white mb-2">{totalRecords}</p>
      <p className="text-sm text-[#7A8694]">records in your vault</p>
      {away && (
        <p className="mt-4 text-lg font-bold" style={{ color: dominantColor }}>
          Only {away} away from {next}!
        </p>
      )}
    </div>
  );
};

const NewAdditionsSlide = ({ additions, dominantColor }) => {
  if (!additions || additions.length === 0) return null;
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 snap-start" data-testid="slide-additions">
      <p className="text-xs font-medium tracking-[0.2em] uppercase mb-6 text-center" style={{ color: dominantColor }}>
        New This Week
      </p>
      <div className="grid grid-cols-2 gap-3 max-w-sm w-full">
        {additions.slice(0, 4).map((r, i) => (
          <div key={i} className="rounded-xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)', animationDelay: `${i * 150}ms` }}>
            <div className="aspect-square overflow-hidden">
              {r.cover_url ? (
                <ReportImg src={r.cover_url} alt={r.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-[#1E2A3A]">
                  <Disc className="w-8 h-8 text-[#3A4D63]" />
                </div>
              )}
            </div>
            <div className="p-2.5">
              <p className="text-xs font-bold text-white truncate">{r.title}</p>
              <p className="text-[10px] text-[#3A4D63] truncate">{r.artist}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Share Card (for export) ───
const ShareCardImg = ({ data, dominantColor }) => {
  const [src, setSrc] = React.useState(() => proxyImageUrl(data.heroRecord?.cover_url));
  const [tried, setTried] = React.useState(0);
  const fallbacks = data.heroFallbacks || [];
  const handleError = () => {
    if (tried < fallbacks.length) {
      setSrc(proxyImageUrl(fallbacks[tried]));
      setTried(t => t + 1);
    }
  };
  if (!src) {
    return <div style={{ width: 480, height: 480, borderRadius: 32, background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Disc style={{ width: 120, height: 120, color: dominantColor, opacity: 0.3 }} />
    </div>;
  }
  return <img src={src} alt="" crossOrigin="anonymous" onError={handleError}
    style={{ width: 480, height: 480, borderRadius: 32, objectFit: 'cover', boxShadow: `0 40px 100px ${dominantColor}40` }} />;
};

const ShareCard = React.forwardRef(({ data, dominantColor }, ref) => (
  <div ref={ref} className="relative overflow-hidden" style={{ width: 1080, height: 1920, background: `linear-gradient(180deg, ${darken(dominantColor, 0.15)} 0%, ${darken(dominantColor, 0.25)} 40%, #0A0A0A 100%)` }}>
    {/* Safe zone top (250px) */}
    <div style={{ paddingTop: 180, textAlign: 'center' }}>
      <p style={{ fontSize: 28, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.5)', fontFamily: '"DM Serif Display", Georgia, serif', textTransform: 'uppercase' }}>
        THE HONEY GROOVE
      </p>
      <p style={{ fontSize: 16, color: 'rgba(255,255,255,0.35)', marginTop: 8 }}>Your Weekly Hive Summary</p>
    </div>
    {/* Center: Album art — proxied for CORS-safe canvas rendering */}
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: 120 }}>
      {data.heroRecord?.cover_url ? (
        <ShareCardImg data={data} dominantColor={dominantColor} />
      ) : (
        <div style={{ width: 480, height: 480, borderRadius: 32, background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Disc style={{ width: 120, height: 120, color: dominantColor, opacity: 0.3 }} />
        </div>
      )}
    </div>
    {/* Record info */}
    <div style={{ textAlign: 'center', marginTop: 48 }}>
      <p style={{ fontSize: 36, fontWeight: 900, color: '#fff' }}>{data.heroRecord?.title || 'Your Week'}</p>
      <p style={{ fontSize: 22, color: 'rgba(255,255,255,0.5)', marginTop: 8 }}>{data.heroRecord?.artist || ''}</p>
    </div>
    {/* Bottom stats (safe zone 300px) */}
    <div style={{ position: 'absolute', bottom: 340, left: 0, right: 0, textAlign: 'center' }}>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 80 }}>
        <div>
          <p style={{ fontSize: 48, fontWeight: 900, color: dominantColor }}>${data.totalValue?.toLocaleString() || '0'}</p>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 4 }}>Total Value</p>
        </div>
        <div>
          <p style={{ fontSize: 48, fontWeight: 900, color: dominantColor }}>{data.totalRecords}</p>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 4 }}>Records</p>
        </div>
      </div>
    </div>
    {/* Branding at very bottom */}
    <div style={{ position: 'absolute', bottom: 80, left: 0, right: 0, textAlign: 'center' }}>
      <Disc style={{ display: 'inline', width: 24, height: 24, color: dominantColor, opacity: 0.4 }} />
    </div>
  </div>
));
ShareCard.displayName = 'ShareCard';

// ─── Fresh Start Fallback ───
const FreshStartSlide = ({ totalValue, dominantColor }) => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-fresh-start">
    <Disc className="w-16 h-16 mb-6" style={{ color: dominantColor, opacity: 0.4 }} />
    <h2 className="text-3xl sm:text-4xl font-black text-white mb-2">A Fresh Start in the Hive</h2>
    <p className="text-sm text-[#7A8694] mb-8">No spins this week. Your collection is waiting.</p>
    {totalValue > 0 && (
      <>
        <p className="text-6xl sm:text-8xl font-black" style={{ color: dominantColor }}>
          ${totalValue.toLocaleString()}
        </p>
        <p className="text-xs text-[#3A4D63] mt-2 tracking-[0.15em] uppercase">Total Collection Value</p>
      </>
    )}
  </div>
);

// ─── Main Page ───
const WeeklyReportPage = () => {
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dominantColor, setDominantColor] = useState('#D4A828');
  const [exporting, setExporting] = useState(false);
  const shareRef = useRef(null);

  useEffect(() => {
    if (!token) return;
    const fetchData = async () => {
      try {
        const [recordsR, spinsR, valR] = await Promise.all([
          axios.get(`${API}/records`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/spins`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/valuation/collection-value`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: {} })),
        ]);
        const records = recordsR.data;
        const spins = spinsR.data;
        const valData = valR.data;
        const week = Date.now() - 7 * 86400000;

        const weekAdds = records.filter(r => new Date(r.created_at) > new Date(week));
        const weekSpins = spins.filter(s => new Date(s.spun_at || s.created_at) > new Date(week));

        // Top spin of the week
        const spinCounts = {};
        weekSpins.forEach(s => { spinCounts[s.record_id] = (spinCounts[s.record_id] || 0) + 1; });
        const topSpinEntry = Object.entries(spinCounts).sort((a, b) => b[1] - a[1])[0];
        const topSpinRecord = topSpinEntry ? records.find(r => r.id === topSpinEntry[0]) : null;
        const topSpinCount = topSpinEntry ? topSpinEntry[1] : 0;

        // If no spins, use most valuable recent addition
        const topAddition = weekAdds.length > 0
          ? weekAdds.sort((a, b) => (b.manual_price || b.median_price || 0) - (a.manual_price || a.median_price || 0))[0]
          : records.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];

        const heroRecord = topSpinRecord || topAddition;
        const isTopSpin = !!topSpinRecord;

        // Build image fallback chain for the hero record
        const heroFallbacks = [];
        if (heroRecord) {
          if (heroRecord.spotify_image_url) heroFallbacks.push(heroRecord.spotify_image_url);
          if (heroRecord.apple_artwork_url) heroFallbacks.push(heroRecord.apple_artwork_url);
        }

        const totalValue = valData.total_value || 0;

        // Date range for header
        const weekEnd = new Date();
        const weekStart = new Date(week);
        const fmt = (d) => d.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
        const dateRange = `${fmt(weekStart)} – ${fmt(weekEnd)}, ${weekEnd.getFullYear()}`;

        setData({
          totalRecords: records.length,
          weekAdds: weekAdds.length,
          weekSpins: weekSpins.length,
          heroRecord,
          heroFallbacks,
          isTopSpin,
          topSpinCount,
          recentAdds: weekAdds.slice(0, 4),
          totalValue,
          valueGained: 0,
          username: user?.username,
          dateRange,
        });

        // Extract dominant color from hero image
        if (heroRecord?.cover_url) {
          extractDominantColor(heroRecord.cover_url).then(setDominantColor);
        }
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchData();
  }, [token, API, user]);

  const handleShare = useCallback(async () => {
    if (!shareRef.current) return;
    setExporting(true);
    try {
      // Pre-flight: ensure hero image is loaded in browser cache via proxy
      if (data?.heroRecord?.cover_url) {
        const proxied = proxyImageUrl(data.heroRecord.cover_url);
        const loaded = await preflightImage(proxied);
        // If primary fails, try fallbacks
        if (!loaded && data.heroFallbacks) {
          for (const fb of data.heroFallbacks) {
            const fbProxied = proxyImageUrl(fb);
            if (fbProxied && await preflightImage(fbProxied)) break;
          }
        }
      }

      // Temporarily show the share card
      shareRef.current.style.display = 'block';
      shareRef.current.style.position = 'fixed';
      shareRef.current.style.left = '-9999px';
      shareRef.current.style.top = '0';

      // Wait a tick for images to render in the DOM
      await new Promise(r => setTimeout(r, 500));

      const canvas = await html2canvas(shareRef.current, {
        width: 1080, height: 1920, scale: 1, useCORS: true, allowTaint: false, backgroundColor: null,
      });

      shareRef.current.style.display = 'none';

      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], `honeygroove-weekly-${Date.now()}.png`, { type: 'image/png' });
        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          await navigator.share({ files: [file], title: 'The Honey Groove — My Week in Wax' });
        } else {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = file.name; a.click();
          URL.revokeObjectURL(url);
        }
        setExporting(false);
      }, 'image/png');
    } catch {
      setExporting(false);
      if (shareRef.current) shareRef.current.style.display = 'none';
    }
  }, [data]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ background: '#0A0A0A' }} data-testid="weekly-report-loading">
        <Disc className="w-12 h-12 animate-spin" style={{ color: '#D4A828' }} />
        <p className="text-sm font-medium tracking-[0.15em] uppercase" style={{ color: '#D4A828' }}>
          Digging through the crates...
        </p>
      </div>
    );
  }

  // No data at all
  if (!data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6" style={{ background: '#0A0A0A', color: '#fff' }}>
        <Disc className="w-16 h-16 mb-4" style={{ color: '#D4A828', opacity: 0.3 }} />
        <p className="text-lg font-bold">No collection data yet</p>
        <p className="text-sm text-[#3A4D63] mt-1">Start adding records to build your weekly story.</p>
        <Button onClick={() => navigate(-1)} className="mt-6 rounded-full" variant="outline">Go Back</Button>
      </div>
    );
  }

  const bgGradient = `linear-gradient(180deg, ${darken(dominantColor, 0.12)} 0%, ${darken(dominantColor, 0.2)} 30%, #0A0A0A 60%, ${darken(dominantColor, 0.1)} 100%)`;
  const hasSpins = data.weekSpins > 0;

  return (
    <div className="relative" style={{ background: bgGradient }} data-testid="weekly-report-page">
      {/* Desktop: Blurred wallpaper background */}
      {data.heroRecord?.cover_url && (
        <div className="fixed inset-0 z-0 hidden lg:block pointer-events-none" aria-hidden="true">
          <ReportImg src={data.heroRecord.cover_url} fallbacks={data.heroFallbacks} alt="" className="w-full h-full object-cover" style={{ filter: 'blur(80px) brightness(0.15)', transform: 'scale(1.2)' }} />
        </div>
      )}

      {/* Content wrapper — centered on desktop */}
      <div className="relative z-10 max-w-lg mx-auto snap-y snap-mandatory" style={{ scrollSnapType: 'y mandatory' }}>
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="fixed top-4 left-4 z-50 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
          style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)' }}
          data-testid="weekly-report-back"
        >
          <ArrowLeft className="w-5 h-5 text-white" />
        </button>

        {/* Slide 1: Intro */}
        <IntroSlide username={data.username} dominantColor={dominantColor} dateRange={data.dateRange} />

        {/* Slide 2: Hero (Top Spin or Fresh Start) */}
        {hasSpins ? (
          <HeroSlide record={data.heroRecord} fallbacks={data.heroFallbacks} spinCount={data.topSpinCount} isTopSpin={data.isTopSpin} dominantColor={dominantColor} />
        ) : (
          <FreshStartSlide totalValue={data.totalValue} dominantColor={dominantColor} />
        )}

        {/* Slide 3: Stats */}
        <StatsSlide stats={data} dominantColor={dominantColor} />

        {/* Slide 4: New Additions */}
        <NewAdditionsSlide additions={data.recentAdds} dominantColor={dominantColor} />

        {/* Slide 6: Milestone */}
        <MilestoneSlide totalRecords={data.totalRecords} dominantColor={dominantColor} />

        {/* Slide 7: Share CTA */}
        <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center snap-start" data-testid="slide-share">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-6" style={{ color: dominantColor }}>
            Share Your Week
          </p>
          <p className="text-lg text-[#7A8694] mb-8 max-w-xs">
            Show the Hive what you've been spinning. Export a ready-to-share story card.
          </p>
          <Button
            onClick={handleShare}
            disabled={exporting}
            className="rounded-full px-8 py-3 text-base font-bold gap-2"
            style={{ background: dominantColor, color: '#0A0A0A' }}
            data-testid="share-week-btn"
          >
            {exporting ? <Disc className="w-5 h-5 animate-spin" /> : <Share2 className="w-5 h-5" />}
            {exporting ? 'Generating...' : 'Share Your Week'}
          </Button>
          <Button
            onClick={() => navigate(-1)}
            variant="ghost"
            className="mt-4 rounded-full text-sm text-[#3A4D63] hover:text-white"
            data-testid="weekly-report-done"
          >
            Back to Profile
          </Button>
        </div>
      </div>

      {/* Hidden Share Card for export (1080x1920) */}
      <div style={{ display: 'none' }}>
        <ShareCard ref={shareRef} data={data} dominantColor={dominantColor} />
      </div>

      {/* Ken Burns CSS */}
      <style>{`
        @keyframes kenBurns {
          0% { transform: scale(1); }
          100% { transform: scale(1.08); }
        }
      `}</style>
    </div>
  );
};

export default WeeklyReportPage;
