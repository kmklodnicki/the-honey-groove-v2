import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Home, Library, TrendingUp, Loader2 } from 'lucide-react';

const WITTY_LINES = [
  "That's a lot of honey on the shelf.",
  "You might want to insure that hive.",
  "Your shelves are sweeter than we expected.",
  "That's some serious vinyl nectar.",
  "Careful - your hive might attract collectors.",
];

const CountUp = ({ end, duration = 1800 }) => {
  const [current, setCurrent] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    if (end <= 0) return;
    const start = 0;
    const startTime = performance.now();
    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(start + (end - start) * eased));
      if (progress < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => { if (ref.current) cancelAnimationFrame(ref.current); };
  }, [end, duration]);

  return <>{current.toLocaleString()}</>;
};

const WelcomeHivePage = () => {
  const { token, API, user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fadeIn, setFadeIn] = useState(false);
  const [wittyLine] = useState(() => WITTY_LINES[Math.floor(Math.random() * WITTY_LINES.length)]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resp = await axios.get(`${API}/welcome-hive-data`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (resp.data.has_seen) {
          navigate('/hive', { replace: true });
          return;
        }
        setData(resp.data);
        // Mark as seen
        await axios.post(`${API}/mark-welcome-seen`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        navigate('/hive', { replace: true });
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [API, token, navigate]);

  useEffect(() => {
    if (!loading && data) {
      const t = setTimeout(() => setFadeIn(true), 100);
      return () => clearTimeout(t);
    }
  }, [loading, data]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF6EE]">
        <Loader2 className="w-8 h-8 animate-spin text-[#C8861A]" />
      </div>
    );
  }

  if (!data) return null;

  const hasValue = data.total_collection_value > 0;

  return (
    <div className="min-h-screen bg-[#FAF6EE] flex flex-col items-center justify-center px-4 py-12">
      <div
        className={`max-w-lg w-full text-center space-y-8 transition-all duration-1000 ${
          fadeIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
        }`}
      >
        {/* Header */}
        <div className="space-y-2">
          <h1
            className="font-heading text-4xl sm:text-5xl text-[#1F1F1F] tracking-tight"
            data-testid="welcome-title"
          >
            Welcome to the Hive
          </h1>
          <p className="text-base text-[#8A6B4A]" data-testid="welcome-subtitle">
            We took a look at your collection... and wow.
          </p>
        </div>

        {/* Value Module */}
        <div
          className="bg-white/70 backdrop-blur-sm rounded-2xl border border-[#C8861A]/15 p-8 shadow-sm"
          data-testid="value-module"
        >
          {hasValue ? (
            <>
              <p className="text-sm text-[#8A6B4A] uppercase tracking-widest mb-2 font-medium">
                Your Collection Value
              </p>
              <p
                className="font-heading text-5xl sm:text-6xl text-[#1F1F1F] tabular-nums"
                data-testid="collection-value"
              >
                $<CountUp end={Math.round(data.total_collection_value)} />
              </p>
              <p
                className="text-base text-[#8A6B4A]/80 mt-4 italic"
                data-testid="witty-line"
              >
                {wittyLine}
              </p>
            </>
          ) : (
            <>
              <p
                className="font-heading text-2xl text-[#1F1F1F] mb-2"
                data-testid="collection-value-fallback"
              >
                Your collection is in the hive.
              </p>
              <p className="text-sm text-[#8A6B4A]/70">
                We're still gathering the honey on its market value.
              </p>
            </>
          )}
        </div>

        {/* Stats Row */}
        <div
          className={`flex items-center justify-center gap-6 flex-wrap transition-all duration-700 delay-500 ${
            fadeIn ? 'opacity-100' : 'opacity-0'
          }`}
          data-testid="stats-row"
        >
          {data.total_records_imported > 0 && (
            <div className="text-center">
              <p className="font-heading text-2xl text-[#1F1F1F]" data-testid="stat-records">
                {data.total_records_imported}
              </p>
              <p className="text-xs text-[#8A6B4A] uppercase tracking-wide">Records Imported</p>
            </div>
          )}
          {data.total_unique_artists > 0 && (
            <div className="text-center">
              <p className="font-heading text-2xl text-[#1F1F1F]" data-testid="stat-artists">
                {data.total_unique_artists}
              </p>
              <p className="text-xs text-[#8A6B4A] uppercase tracking-wide">Artists Collected</p>
            </div>
          )}
          {data.top_artist_by_count && (
            <div className="text-center">
              <p className="font-heading text-lg text-[#1F1F1F] truncate max-w-[180px]" data-testid="stat-top-artist">
                {data.top_artist_by_count}
              </p>
              <p className="text-xs text-[#8A6B4A] uppercase tracking-wide">Top Artist</p>
            </div>
          )}
        </div>

        {/* CTA Buttons */}
        <div
          className={`flex flex-col sm:flex-row items-center justify-center gap-3 pt-2 transition-all duration-700 delay-700 ${
            fadeIn ? 'opacity-100' : 'opacity-0'
          }`}
          data-testid="cta-buttons"
        >
          <Button
            onClick={() => navigate('/hive')}
            className="bg-[#C8861A] text-white hover:bg-[#A66F15] rounded-full px-6 gap-2 w-full sm:w-auto"
            data-testid="cta-explore-hive"
          >
            <Home className="w-4 h-4" />
            Explore the Hive
          </Button>
          <Button
            onClick={() => navigate('/collection')}
            variant="outline"
            className="border-[#C8861A]/30 text-[#1F1F1F] hover:bg-[#C8861A]/10 rounded-full px-6 gap-2 w-full sm:w-auto"
            data-testid="cta-view-collection"
          >
            <Library className="w-4 h-4" />
            View Your Collection
          </Button>
          <Button
            onClick={() => navigate('/nectar')}
            variant="outline"
            className="border-[#C8861A]/30 text-[#1F1F1F] hover:bg-[#C8861A]/10 rounded-full px-6 gap-2 w-full sm:w-auto"
            data-testid="cta-market-trends"
          >
            <TrendingUp className="w-4 h-4" />
            Check Market Trends
          </Button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeHivePage;
