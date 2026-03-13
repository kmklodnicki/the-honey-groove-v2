import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Progress } from '../components/ui/progress';
import { Loader2, Disc } from 'lucide-react';
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

const BuildingHivePage = () => {
  const { token, API, updateUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [progress, setProgress] = useState({ status: 'starting', total: 0, imported: 0, skipped: 0 });
  const [messageIndex, setMessageIndex] = useState(0);
  const [fadeIn, setFadeIn] = useState(false);
  const importStarted = useRef(false);

  // Cycle through building messages
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % BUILDING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Fade in on mount
  useEffect(() => {
    const t = setTimeout(() => setFadeIn(true), 100);
    return () => clearTimeout(t);
  }, []);

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
              try {
                await axios.put(`${API}/auth/me`, { onboarding_completed: true }, {
                  headers: { Authorization: `Bearer ${token}` }
                });
                updateUser(prev => ({ ...prev, onboarding_completed: true }));
              } catch { /* non-blocking */ }
              navigate('/onboarding/welcome-to-the-hive', { replace: true });
            } else if (resp.data.status === 'completed' && resp.data.imported === 0) {
              toast.info('No new records to import — your collection is already in sync.');
              navigate('/hive', { replace: true });
            } else if (resp.data.status === 'error') {
              toast.error(resp.data.error_message || 'Import failed. Please try again from your collection page.');
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
  }, [searchParams, API, token, navigate, updateUser]);

  const progressPercent = progress.total > 0
    ? Math.round(((progress.imported + progress.skipped) / progress.total) * 100)
    : 0;

  const username = searchParams.get('username') || '';

  return (
    <div className="min-h-screen bg-[#FAF6EE] flex flex-col items-center justify-center px-4 py-12">
      <div
        className={`max-w-md w-full text-center space-y-8 transition-all duration-1000 ${
          fadeIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
        }`}
      >
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

        {/* Subtle message */}
        <p className="text-xs text-[#8A6B4A]/50">
          This usually takes about a minute. Don't close this tab.
        </p>
      </div>
    </div>
  );
};

export default BuildingHivePage;
