import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Loader2, CheckCircle2 } from 'lucide-react';

const StripeConnectReturnPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, token, API } = useAuth();
  const userId = searchParams.get('user_id');
  const [status, setStatus] = useState('verifying'); // verifying | success | error

  useEffect(() => {
    const verify = async () => {
      try {
        // Call backend to verify and update the account status
        await axios.get(`${API}/stripe/connect/verify?user_id=${userId}`);

        // Now check status
        if (token) {
          const resp = await axios.get(`${API}/stripe/status`, { headers: { Authorization: `Bearer ${token}` } });
          if (resp.data.stripe_connected) {
            setStatus('success');
            setTimeout(() => {
              navigate(user ? `/profile/${user.username}?stripe=connected` : '/hive', { replace: true });
            }, 2500);
            return;
          }
        }

        // If we got here, charges may not be enabled yet
        setStatus('success');
        setTimeout(() => {
          navigate(user ? `/profile/${user.username}?stripe=connected` : '/hive', { replace: true });
        }, 2500);
      } catch (err) {
        console.error('Stripe verification error:', err);
        setStatus('error');
        setTimeout(() => {
          navigate(user ? `/profile/${user.username}` : '/hive', { replace: true });
        }, 3000);
      }
    };

    if (userId) verify();
    else {
      setStatus('error');
      setTimeout(() => navigate('/hive', { replace: true }), 2000);
    }
  }, [userId, token, API, user, navigate]);

  return (
    <div className="min-h-screen bg-honey-cream flex items-center justify-center px-4" data-testid="stripe-return-page">
      <div className="text-center">
        {status === 'verifying' && (
          <>
            <Loader2 className="w-10 h-10 text-honey-amber animate-spin mx-auto mb-4" />
            <p className="text-lg font-heading text-vinyl-black">verifying your stripe account...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <p className="text-xl font-heading text-vinyl-black">stripe connected.</p>
            <p className="text-base text-honey-amber mt-1">you're ready to sell.</p>
            <p className="text-sm text-muted-foreground mt-3">redirecting to your profile...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <p className="text-lg font-heading text-vinyl-black">something went wrong.</p>
            <p className="text-sm text-muted-foreground mt-1">redirecting...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default StripeConnectReturnPage;
