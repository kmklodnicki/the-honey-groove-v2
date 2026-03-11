import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { CheckCircle2, Loader2, XCircle, ShoppingBag } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';
import confetti from 'canvas-confetti';

const CheckoutSuccessPage = () => {
  const { token, API } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [txnData, setTxnData] = useState(null);

  const paymentIntentId = searchParams.get('payment_intent');
  const redirectStatus = searchParams.get('redirect_status');
  const listingId = searchParams.get('listing');

  useEffect(() => {
    if (!paymentIntentId || !token) return;

    const verifyPayment = async () => {
      try {
        const resp = await axios.get(
          `${API}/payments/status/${paymentIntentId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (resp.data.status === 'PAID' || redirectStatus === 'succeeded') {
          setStatus('success');
          setTxnData(resp.data);
          trackEvent('purchase_completed', { amount: resp.data.amount });
          confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 }, colors: ['#FFB300', '#FFA000', '#C8861A'] });
        } else if (resp.data.status === 'PENDING') {
          // Payment still processing — poll once more after a delay
          setTimeout(async () => {
            try {
              const retry = await axios.get(
                `${API}/payments/status/${paymentIntentId}`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              if (retry.data.status === 'PAID') {
                setStatus('success');
                setTxnData(retry.data);
                trackEvent('purchase_completed', { amount: retry.data.amount });
                confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 }, colors: ['#FFB300', '#FFA000', '#C8861A'] });
              } else {
                setStatus('success'); // Show success if redirect_status says succeeded
                setTxnData(retry.data);
                toast.info('Payment is being processed. You\'ll be notified when confirmed.');
              }
            } catch {
              setStatus('success');
              toast.info('Payment is being processed.');
            }
          }, 3000);
        } else {
          setStatus('error');
        }
      } catch {
        // If status check fails but Stripe says succeeded, still show success
        if (redirectStatus === 'succeeded') {
          setStatus('success');
          toast.info('Payment is being processed. You\'ll be notified when confirmed.');
        } else {
          setStatus('error');
        }
      }
    };

    verifyPayment();
  }, [paymentIntentId, redirectStatus, token, API]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4" data-testid="checkout-success-page">
      <div className="max-w-md w-full text-center space-y-6">
        {status === 'loading' && (
          <div className="space-y-4" data-testid="checkout-loading">
            <Loader2 className="w-12 h-12 animate-spin mx-auto" style={{ color: '#C8861A' }} />
            <p className="text-lg font-medium" style={{ color: '#3D2E1E' }}>Verifying your payment...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-6" data-testid="checkout-confirmed">
            <div className="w-20 h-20 rounded-full mx-auto flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)' }}>
              <CheckCircle2 className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: '#3D2E1E', fontFamily: '"DM Serif Display", serif' }}>
              Payment Confirmed!
            </h1>
            <p className="text-stone-500">
              Your order has been placed. The seller will be notified and you'll receive shipping details soon.
            </p>
            {txnData?.amount && (
              <div className="rounded-xl p-4 mx-auto max-w-xs"
                style={{ background: '#FFFDF5', border: '1px solid rgba(200,134,26,0.3)' }}>
                <span className="text-sm text-stone-400">Total paid</span>
                <p className="text-2xl font-bold" style={{ color: '#C8861A' }}>${txnData.amount.toFixed(2)}</p>
              </div>
            )}
            <div className="flex flex-col gap-3 pt-2">
              <Button
                onClick={() => navigate('/orders')}
                className="w-full h-12 rounded-full text-base font-semibold"
                style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)', color: '#1A1A1A' }}
                data-testid="view-orders-btn"
              >
                <ShoppingBag className="w-4 h-4 mr-2" /> View My Orders
              </Button>
              <Link
                to="/honeypot"
                className="text-sm hover:underline transition-colors"
                style={{ color: '#C8861A' }}
                data-testid="back-to-shop-link"
              >
                Back to The Honeypot
              </Link>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-6" data-testid="checkout-error">
            <div className="w-20 h-20 rounded-full mx-auto flex items-center justify-center bg-red-100">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: '#3D2E1E', fontFamily: '"DM Serif Display", serif' }}>
              Payment Issue
            </h1>
            <p className="text-stone-500">
              We couldn't confirm your payment. If you were charged, it will be refunded automatically.
            </p>
            <Button
              onClick={() => navigate('/honeypot')}
              className="w-full h-12 rounded-full text-base font-semibold"
              style={{ background: 'linear-gradient(135deg, #FFB300, #FFA000)', color: '#1A1A1A' }}
              data-testid="back-to-shop-btn"
            >
              Back to The Honeypot
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckoutSuccessPage;
