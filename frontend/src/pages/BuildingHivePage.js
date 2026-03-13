import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Progress } from '../components/ui/progress';
import { Button } from '../components/ui/button';
import { Loader2, Disc, CheckCircle2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const BUILDING_MESSAGES = [
  'Dusting off the crates...',
  'Sorting your wax...',
  'Cataloging every groove...',
  'Polishing the rare finds...',
  'Stacking the shelves...',
  'Spinning up the database...',
  'Almost there, honey...',
];

const CONFETTI_COLORS = ['#FFD700', '#C8861A', '#DAA520', '#FF8C00', '#8B4513', '#F4B521', '#FFB800'];

const ConfettiPiece = ({ delay, left }) => (
  <div
    className="absolute w-2 h-2 rounded-sm opacity-0"
    style={{
      left: `${left}%`,
      top: '-8px',
      backgroundColor: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      animation: `confettiFall 2.5s ease-in ${delay}s forwards`,
      transform: `rotate(${Math.random() * 360}deg)`,
    }}
  />
);

const BuildingHivePage = () => {
  const { token, API, updateUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [progress, setProgress] = useState({ status: 'starting', total: 0, imported: 0, skipped: 0 });
  const [messageIndex, setMessageIndex] = useState(0);
  const [fadeIn, setFadeIn] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const importStarted = useRef(false);

  // Cycle through building messages
  useEffect(() => {
    if (showSuccess) return;
    const interval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % BUILDING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [showSuccess]);

  // Fade in on mount
  useEffect(() => {
    const t = setTimeout(() => setFadeIn(true), 100);
    return () => clearTimeout(t);
  }, []);

  const handleImportComplete = useCallback(async (importData) => {
    // Set has_connected_discogs + onboarding_completed
    try {
      await axios.put(`${API}/auth/me`, {
        onboarding_completed: true,
        has_connected_discogs: true,
      }, { headers: { Authorization: `Bearer ${token}` } });
      updateUser(prev => ({ ...prev, onboarding_completed: true, has_connected_discogs: true }));
    } catch { /* non-blocking */ }
    setProgress(importData);
    setShowSuccess(true);
  }, [API, token, updateUser]);

  // Auto-start import on mount if discogs=connected
  useEffect(() => {
    if (importStarted.current) return;
    const discogsParam = searchParams.get('discogs');
    if (discogsParam !== 'connected') {
      navigate('/hive', { replace: true });
      return;
    }
    importStarted.current = true;

    const poll = () => {
      const interval = setInterval(async () => {
        try {
          const resp = await axios.get(`${API}/discogs/import/progress`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setProgress(resp.data);

          if (resp.data.status === 'completed' || resp.data.status === 'error') {
            clearInterval(interval);
            if (resp.data.status === 'completed' && resp.data.imported > 0) {
              handleImportComplete(resp.data);
            } else if (resp.data.status === 'completed' && resp.data.imported === 0) {
              toast.info('No new records to import — your vault is already in sync.');
              navigate('/hive', { replace: true });
            } else if (resp.data.status === 'error') {
              toast.error(resp.data.error_message || 'Import failed. Please try again from your vault page.');
              navigate('/collection', { replace: true });
            }
          }
        } catch { /* ignore poll errors */ }
      }, 2000);
    };

    const startAndPoll = async () => {
      try {
        await axios.post(`${API}/discogs/import`, {}, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 30000,
        });
      } catch (err) {
        if (err.response?.status !== 409) {
          toast.error(err.response?.data?.detail || 'Failed to start import');
        }
      }
      poll();
    };

    startAndPoll();
  }, [searchParams, API, token, navigate, handleImportComplete]);

  const progressPercent = progress.total > 0
    ? Math.round(((progress.imported + progress.skipped) / progress.total) * 100)
    : 0;

  const username = searchParams.get('username') || '';

  return (
    <div className="min-h-screen bg-[#FAF6EE] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Confetti CSS */}
      <style>{`
        @keyframes confettiFall {
          0% { opacity: 1; transform: translateY(0) rotate(0deg); }
          100% { opacity: 0; transform: translateY(100vh) rotate(720deg); }
        }
        @keyframes successPop {
          0% { transform: scale(0.5); opacity: 0; }
          60% { transform: scale(1.05); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>

      {/* Confetti layer */}
      {showSuccess && (
        <div className="fixed inset-0 pointer-events-none z-50" data-testid="confetti-layer">
          {Array.from({ length: 60 }).map((_, i) => (
            <ConfettiPiece key={i} delay={Math.random() * 1.5} left={Math.random() * 100} />
          ))}
        </div>
      )}

      <div
        className={`max-w-md w-full text-center space-y-8 transition-all duration-1000 ${
          fadeIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
        }`}
      >
        {/* SUCCESS STATE */}
        {showSuccess ? (
          <div
            className="space-y-6"
            style={{ animation: 'successPop 0.5s ease-out forwards' }}
            data-testid="import-success-popup"
          >
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-green-600" />
              </div>
            </div>

            <div className="space-y-2">
              <h1
                className="font-heading text-3xl sm:text-4xl text-[#1F1F1F] tracking-tight"
                style={{ fontFamily: '"Playfair Display", serif' }}
                data-testid="success-title"
              >
                Collection Connected!
              </h1>
              <p className="text-[#8A6B4A] text-base" data-testid="success-summary">
                <span className="font-semibold text-[#C8861A]">{progress.imported}</span> records imported
                {progress.skipped > 0 && <span className="text-[#8A6B4A]/60"> ({progress.skipped} already in your vault)</span>}
              </p>
              {username && (
                <p className="text-sm text-[#8A6B4A]/60">
                  Connected as @{username} on Discogs
                </p>
              )}
            </div>

            <Button
              onClick={() => navigate('/hive', { replace: true })}
              className="w-full max-w-xs mx-auto rounded-full py-6 gap-2 font-bold text-base"
              style={{ background: 'linear-gradient(135deg, #FFD700, #F4B521)', color: '#1A1A1A', border: '1.5px solid #DAA520' }}
              data-testid="start-spinning-btn"
            >
              <Sparkles className="w-5 h-5" />
              Start Spinning
            </Button>
          </div>
        ) : (
          /* LOADING STATE */
          <>
            {/* Spinning disc animation */}
            <div className="flex justify-center" data-testid="building-hive-disc">
              <div className="relative w-24 h-24">
                <div className="absolute inset-0 rounded-full border-4 border-[#C8861A]/20" />
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#C8861A] animate-spin" style={{ animationDuration: '2s' }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Disc className="w-10 h-10 text-[#C8861A]" />
                </div>
              </div>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <h1
                className="font-heading text-3xl sm:text-4xl text-[#1F1F1F] tracking-tight"
                style={{ fontFamily: '"Playfair Display", serif' }}
                data-testid="building-hive-title"
              >
                Building your Hive...
              </h1>
              {username && (
                <p className="text-sm text-[#8A6B4A]" data-testid="building-hive-username">
                  Connected as <span className="font-medium">@{username}</span> on Discogs
                </p>
              )}
            </div>

            {/* Progress bar */}
            <div className="space-y-3 px-4" data-testid="building-hive-progress">
              <Progress value={progressPercent} className="h-2" />
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#8A6B4A] flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {BUILDING_MESSAGES[messageIndex]}
                </span>
                {progress.total > 0 && (
                  <span className="text-[#8A6B4A]/70 tabular-nums text-xs">
                    {progress.imported + progress.skipped} / {progress.total}
                  </span>
                )}
              </div>
              {progress.imported > 0 && (
                <div className="flex gap-4 justify-center text-xs text-[#8A6B4A]/60">
                  <span className="text-green-600">{progress.imported} imported</span>
                  {progress.skipped > 0 && <span>{progress.skipped} skipped</span>}
                </div>
              )}
            </div>

            <p className="text-xs text-[#8A6B4A]/50">
              This usually takes about a minute. Don't close this tab.
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default BuildingHivePage;
