import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Disc, ArrowLeft, Play, Sparkles, TrendingUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import AlbumArt from '../components/AlbumArt';

const WeeklyReportPage = () => {
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const fetchData = async () => {
      try {
        const [recordsR, spinsR] = await Promise.all([
          axios.get(`${API}/records`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/spins`, { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        const records = recordsR.data;
        const spins = spinsR.data;
        const week = Date.now() - 7 * 86400000;

        const weekAdds = records.filter(r => new Date(r.created_at) > new Date(week));
        const weekSpins = spins.filter(s => new Date(s.spun_at || s.created_at) > new Date(week));

        // Top spin of the week
        const spinCounts = {};
        weekSpins.forEach(s => {
          const key = s.record_id;
          spinCounts[key] = (spinCounts[key] || 0) + 1;
        });
        const topSpinId = Object.entries(spinCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
        const topSpinRecord = records.find(r => r.id === topSpinId);

        setData({
          totalRecords: records.length,
          weekAdds: weekAdds.length,
          weekSpins: weekSpins.length,
          topSpin: topSpinRecord,
          topSpinCount: spinCounts[topSpinId] || 0,
          recentAdds: weekAdds.slice(0, 4),
          username: user?.username,
        });
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchData();
  }, [token, API, user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0A0A0A' }}>
        <Disc className="w-12 h-12 animate-spin" style={{ color: '#FFD700' }} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6" style={{ background: '#0A0A0A', color: '#fff' }}>
        <p className="text-lg font-bold">No data yet</p>
        <Button onClick={() => navigate(-1)} className="mt-4 rounded-full" variant="outline">Go Back</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(180deg, #0A0A0A 0%, #1A0F00 50%, #0A0A0A 100%)' }} data-testid="weekly-report-page">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="fixed top-4 left-4 z-50 w-10 h-10 rounded-full flex items-center justify-center bg-white/10 hover:bg-white/20 transition-colors"
        data-testid="weekly-report-back"
      >
        <ArrowLeft className="w-5 h-5 text-white" />
      </button>

      {/* Hero: Top Spin */}
      <div className="flex flex-col items-center pt-20 px-6 pb-10 text-center">
        <p className="text-xs font-medium tracking-[0.2em] uppercase mb-6" style={{ color: '#C8861A' }}>
          {data.username ? `@${data.username}'s` : 'Your'} Week in Wax
        </p>

        {data.topSpin ? (
          <>
            <p className="text-sm text-stone-400 mb-4">Top Spin of the Week</p>
            <div className="w-56 h-56 sm:w-72 sm:h-72 rounded-2xl overflow-hidden shadow-2xl mb-6 ring-2 ring-[#FFD700]/30" data-testid="weekly-top-spin-art">
              <AlbumArt
                src={data.topSpin.cover_url}
                alt={`${data.topSpin.artist} - ${data.topSpin.title}`}
                className="w-full h-full object-cover"
                artist={data.topSpin.artist}
                title={data.topSpin.title}
              />
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white leading-tight" data-testid="weekly-top-spin-title">
              {data.topSpin.title}
            </h2>
            <p className="text-base text-stone-400 mt-1">{data.topSpin.artist}</p>
            <div className="flex items-center gap-2 mt-3">
              <Play className="w-4 h-4" style={{ color: '#FFD700' }} />
              <span className="text-sm font-bold" style={{ color: '#FFD700' }}>
                {data.topSpinCount} spin{data.topSpinCount !== 1 ? 's' : ''} this week
              </span>
            </div>
          </>
        ) : (
          <>
            <div className="w-40 h-40 rounded-2xl flex items-center justify-center mb-6" style={{ background: 'rgba(255,215,0,0.1)' }}>
              <Disc className="w-16 h-16" style={{ color: '#FFD700', opacity: 0.3 }} />
            </div>
            <h2 className="text-2xl font-black text-white">No Spins This Week</h2>
            <p className="text-sm text-stone-400 mt-1">Drop the needle and start your story.</p>
          </>
        )}
      </div>

      {/* Stats strip */}
      <div className="flex justify-center gap-8 py-8 px-6" data-testid="weekly-stats-strip">
        <div className="text-center">
          <p className="text-3xl sm:text-4xl font-black" style={{ color: '#FFD700' }}>{data.weekSpins}</p>
          <p className="text-xs text-stone-500 mt-1 tracking-wide uppercase">Spins</p>
        </div>
        <div className="text-center">
          <p className="text-3xl sm:text-4xl font-black" style={{ color: '#FFD700' }}>{data.weekAdds}</p>
          <p className="text-xs text-stone-500 mt-1 tracking-wide uppercase">Added</p>
        </div>
        <div className="text-center">
          <p className="text-3xl sm:text-4xl font-black" style={{ color: '#FFD700' }}>{data.totalRecords}</p>
          <p className="text-xs text-stone-500 mt-1 tracking-wide uppercase">Total</p>
        </div>
      </div>

      {/* Recent Additions */}
      {data.recentAdds.length > 0 && (
        <div className="px-6 py-8">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4" style={{ color: '#C8861A' }} />
            <p className="text-xs font-medium tracking-[0.15em] uppercase text-stone-400">New This Week</p>
          </div>
          <div className="grid grid-cols-2 gap-3" data-testid="weekly-recent-adds">
            {data.recentAdds.map(r => (
              <div key={r.id} className="rounded-xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <div className="aspect-square">
                  <AlbumArt src={r.cover_url} alt={r.title} className="w-full h-full object-cover" artist={r.artist} title={r.title} />
                </div>
                <div className="p-2.5">
                  <p className="text-xs font-bold text-white truncate">{r.title}</p>
                  <p className="text-[10px] text-stone-500 truncate">{r.artist}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Vibe footer */}
      <div className="text-center pb-16 pt-4 px-6">
        <TrendingUp className="w-6 h-6 mx-auto mb-3" style={{ color: '#C8861A' }} />
        <p className="text-xs text-stone-500">
          {data.weekSpins > 10 ? 'Heavy rotation week. The groove is strong.' :
           data.weekSpins > 3 ? 'Steady listening. Quality over quantity.' :
           'Quiet week. The vinyl is waiting.'}
        </p>
        <Button
          onClick={() => navigate(-1)}
          variant="outline"
          className="mt-6 rounded-full text-xs border-stone-700 text-stone-400 hover:text-white hover:border-stone-500"
          data-testid="weekly-report-done"
        >
          Back to Profile
        </Button>
      </div>
    </div>
  );
};

export default WeeklyReportPage;
