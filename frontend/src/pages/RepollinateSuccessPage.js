import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

const CONFETTI_COLORS = ['#FFD700', '#FFA500', '#FFB800', '#C8861A', '#E5AB00', '#FDE68A', '#DAA520'];

const ConfettiPiece = ({ delay, left }) => {
  const color = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
  const size = 6 + Math.random() * 8;
  const duration = 2 + Math.random() * 2;
  const rotation = Math.random() * 360;
  return (
    <div
      className="absolute top-0 animate-bounce"
      style={{
        left: `${left}%`,
        width: size,
        height: size * (0.5 + Math.random() * 0.5),
        background: color,
        borderRadius: Math.random() > 0.5 ? '50%' : '2px',
        transform: `rotate(${rotation}deg)`,
        animation: `confettiFall ${duration}s ease-in ${delay}s forwards`,
        opacity: 0,
      }}
    />
  );
};

const RepollinateSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { token, API, refreshUser } = useAuth();
  const [status, setStatus] = useState('verifying');
  const [streak, setStreak] = useState(null);

  const sessionId = searchParams.get('session_id');

  const verify = useCallback(async () => {
    if (!sessionId || !token) return;
    try {
      const res = await axios.get(`${API}/repollinate/success?session_id=${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.data.restored) {
        setStreak(res.data.streak);
        setStatus('success');
        if (refreshUser) refreshUser();
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  }, [sessionId, token, API, refreshUser]);

  useEffect(() => { verify(); }, [verify]);

  useEffect(() => {
    if (status === 'success') {
      const timer = setTimeout(() => navigate('/hive'), 5000);
      return () => clearTimeout(timer);
    }
  }, [status, navigate]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <style>{`
        @keyframes confettiFall {
          0% { opacity: 1; transform: translateY(-20px) rotate(0deg); }
          100% { opacity: 0; transform: translateY(100vh) rotate(720deg); }
        }
      `}</style>

      {status === 'success' && (
        <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
          {Array.from({ length: 60 }).map((_, i) => (
            <ConfettiPiece key={i} delay={Math.random() * 1.5} left={Math.random() * 100} />
          ))}
        </div>
      )}

      <div className="text-center max-w-md" data-testid="repollinate-success">
        {status === 'verifying' && (
          <>
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4" style={{ color: '#C8861A' }} />
            <h2 className="font-heading text-2xl" style={{ fontFamily: '"Playfair Display", serif' }}>Verifying payment...</h2>
            <p className="text-sm text-muted-foreground mt-2">Just a moment while we restore your streak.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-6xl mb-4">🐝</div>
            <h2 className="font-heading text-3xl mb-2" style={{ fontFamily: '"Playfair Display", serif', color: '#915527' }}>
              You've re-pollinated!
            </h2>
            <p className="text-lg mb-1" style={{ color: '#C8861A' }}>
              Your streak has been restored.
            </p>
            {streak && (
              <div
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full mt-4 text-sm font-bold"
                style={{ background: '#FDE68A', color: '#915527' }}
                data-testid="restored-streak-badge"
              >
                {streak} day streak restored
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-4">Redirecting to The Hive in 5 seconds...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">😔</div>
            <h2 className="font-heading text-2xl mb-2" style={{ fontFamily: '"Playfair Display", serif' }}>Something went wrong</h2>
            <p className="text-sm text-muted-foreground mb-4">We couldn't verify your payment. Please contact support if you were charged.</p>
            <button
              onClick={() => navigate('/hive')}
              className="px-6 py-2 rounded-full text-sm font-bold"
              style={{ background: '#FDE68A', color: '#915527' }}
              data-testid="repollinate-error-back"
            >
              Back to The Hive
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default RepollinateSuccessPage;
