import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { TurntableErrorScreen } from './ErrorBoundary';
import { API_BASE } from '../utils/apiBase';

const API = `${API_BASE}/api`;

// Intercepts 500/503 API responses and shows the turntable error screen
export const ApiErrorGate = ({ children }) => {
  const [serverDown, setServerDown] = useState(false);
  const failCountRef = useRef(0);

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => {
        // Successful response resets the fail counter
        failCountRef.current = 0;
        return response;
      },
      (error) => {
        const status = error?.response?.status;
        // Count consecutive 500/503 errors; show gate after 2+ to avoid false alarms
        if (status === 500 || status === 503) {
          failCountRef.current += 1;
          if (failCountRef.current >= 2) {
            setServerDown(true);
          }
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const handleRetry = useCallback(() => {
    failCountRef.current = 0;
    setServerDown(false);
    window.location.reload();
  }, []);

  if (serverDown) {
    return (
      <TurntableErrorScreen
        title="Don't skip a beat!"
        subtitle="Our needle hit a little dust. We're auto-cleaning the grooves right now — try refreshing in a moment!"
        actionLabel="Try Again"
        onAction={handleRetry}
      />
    );
  }

  return children;
};

// Checks maintenance mode on app load and periodically
export const MaintenanceGate = ({ children }) => {
  const [maintenance, setMaintenance] = useState(false);
  const [checked, setChecked] = useState(false);

  const checkMaintenance = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/status/maintenance`, { timeout: 5000 });
      setMaintenance(res.data?.maintenance_mode === true);
    } catch {
      // If the check itself fails, don't block — let ApiErrorGate handle it
    }
    setChecked(true);
  }, []);

  useEffect(() => {
    checkMaintenance();
    // Re-check every 60 seconds
    const interval = setInterval(checkMaintenance, 60000);
    return () => clearInterval(interval);
  }, [checkMaintenance]);

  // Don't block rendering until we've checked
  if (!checked) return children;

  // Admins bypass maintenance — check localStorage for cached admin status
  if (maintenance) {
    try {
      const isAdmin = localStorage.getItem('honeygroove_is_admin') === 'true';
      if (isAdmin) return children;
    } catch {}

    return (
      <TurntableErrorScreen
        title="Tuning up the grooves"
        subtitle="We're making some improvements behind the scenes. The hive will be back shortly — hang tight!"
        actionLabel="Check Again"
        onAction={() => { setChecked(false); checkMaintenance(); }}
      />
    );
  }

  return children;
};
