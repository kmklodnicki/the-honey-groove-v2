import React, { useState, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, ExpressCheckoutElement, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Loader2, CreditCard, ShieldCheck, Lock } from 'lucide-react';
import { Button } from './ui/button';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const CheckoutForm = ({ amount, listingId, onSuccess, onCancel }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState(null);

  const handleExpressCheckout = useCallback(async ({ expressPaymentType }) => {
    setPaymentMethod(expressPaymentType);
  }, []);

  const handleExpressConfirm = useCallback(async () => {
    if (!stripe || !elements) return;
    setProcessing(true);
    setError(null);
    const { error: confirmError } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: `${window.location.origin}/honeypot/checkout/success?listing=${listingId}` },
    });
    if (confirmError) {
      setError(confirmError.message);
      setProcessing(false);
    }
  }, [stripe, elements, listingId]);

  const handleCardSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    setProcessing(true);
    setError(null);
    const { error: confirmError } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: `${window.location.origin}/honeypot/checkout/success?listing=${listingId}` },
    });
    if (confirmError) {
      setError(confirmError.message);
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="express-checkout-form">
      {/* Express wallets: Apple Pay / Google Pay */}
      <div data-testid="express-wallet-buttons">
        <ExpressCheckoutElement
          onConfirm={handleExpressConfirm}
          onClick={handleExpressCheckout}
          options={{
            buttonType: { applePay: 'buy', googlePay: 'buy' },
            buttonTheme: { applePay: 'black', googlePay: 'black' },
            layout: { maxColumns: 2, maxRows: 1, overflow: 'never' },
          }}
        />
      </div>

      {/* OR divider */}
      <div className="flex items-center gap-3 py-1">
        <div className="flex-1 h-px" style={{ background: 'rgba(200,134,26,0.3)' }} />
        <span className="text-xs font-medium text-stone-400 uppercase tracking-widest">or pay with card</span>
        <div className="flex-1 h-px" style={{ background: 'rgba(200,134,26,0.3)' }} />
      </div>

      {/* Manual card payment */}
      <form onSubmit={handleCardSubmit}>
        <div className="rounded-lg p-4" style={{ border: '1px solid rgba(200,134,26,0.3)', background: '#FFFDF5' }}>
          <PaymentElement options={{ layout: 'tabs' }} />
        </div>

        {error && (
          <div className="mt-3 px-3 py-2 rounded-lg text-sm text-red-700 bg-red-50 border border-red-200" data-testid="checkout-error">
            {error}
          </div>
        )}

        <Button
          type="submit"
          disabled={processing || !stripe}
          className="w-full mt-4 h-12 rounded-full text-base font-semibold"
          style={{ background: processing ? '#ccc' : 'linear-gradient(135deg, #FFB300, #FFA000)', color: '#1A1A1A' }}
          data-testid="card-pay-btn"
        >
          {processing ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Processing...</>
          ) : (
            <><CreditCard className="w-4 h-4 mr-2" /> Pay ${amount.toFixed(2)}</>
          )}
        </Button>
      </form>

      <div className="flex items-center justify-center gap-2 text-xs text-stone-400">
        <Lock className="w-3 h-3" />
        <span>Secured by Stripe</span>
        <ShieldCheck className="w-3 h-3 ml-2" />
        <span>Buyer Protection</span>
      </div>

      <button
        onClick={onCancel}
        className="w-full text-center text-sm text-stone-400 hover:text-stone-600 transition-colors py-2"
        data-testid="checkout-cancel"
      >
        Cancel
      </button>
    </div>
  );
};


const ExpressCheckout = ({ clientSecret, amount, listingId, onSuccess, onCancel }) => {
  if (!clientSecret) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#C8861A' }} />
        <span className="ml-2 text-stone-500">Preparing checkout...</span>
      </div>
    );
  }

  const options = {
    clientSecret,
    appearance: {
      theme: 'stripe',
      variables: {
        colorPrimary: '#C8861A',
        colorBackground: '#FFFDF5',
        fontFamily: '"DM Sans", system-ui, sans-serif',
        borderRadius: '8px',
      },
    },
  };

  return (
    <Elements stripe={stripePromise} options={options}>
      <CheckoutForm
        amount={amount}
        listingId={listingId}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />
    </Elements>
  );
};

export default ExpressCheckout;
