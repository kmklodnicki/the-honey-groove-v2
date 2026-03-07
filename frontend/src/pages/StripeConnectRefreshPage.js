import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

const StripeConnectRefreshPage = () => {
  const [searchParams] = useSearchParams();
  const { token, API } = useAuth();
  const userId = searchParams.get('user_id');
  const [error, setError] = useState(null);

  useEffect(() => {
    const refresh = async () => {
      try {
        // Call backend to get a new onboarding URL
        const resp = await axios.get(`${API}/stripe/connect/refresh-link?user_id=${userId}`);
        if (resp.data.url) {
          window.location.href = resp.data.url;
        } else {
          setError('Could not generate new onboarding link.');
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to refresh onboarding link.');
      }
    };

    if (userId) refresh();
    else setError('Missing user information.');
  }, [userId, token, API]);

  return (
    <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4" data-testid="stripe-refresh-page">
      <div className="text-center">
        {!error ? (
          <>
            <Loader2 className="w-10 h-10 text-honey-amber animate-spin mx-auto mb-4" />
            <p className="text-lg font-heading text-vinyl-black">resuming stripe setup...</p>
          </>
        ) : (
          <p className="text-lg text-red-600">{error}</p>
        )}
      </div>
    </div>
  );
};

export default StripeConnectRefreshPage;
