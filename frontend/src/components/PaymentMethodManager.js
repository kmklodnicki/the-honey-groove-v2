import React, { useState, useEffect, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from './ui/button';
import { Loader2, CreditCard, Trash2, CheckCircle2, Plus, Star } from 'lucide-react';
import { toast } from 'sonner';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '15px',
      color: '#1E2A3A',
      fontFamily: 'Inter, sans-serif',
      '::placeholder': { color: '#9ca3af' },
    },
    invalid: { color: '#ef4444' },
  },
};

const AddCardForm = ({ onAdded, onCancel }) => {
  const stripe = useStripe();
  const elements = useElements();
  const { token, API } = useAuth();
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    setSaving(true);
    try {
      // 1. Get SetupIntent client_secret
      const { data: siData } = await axios.post(
        `${API}/payments/setup-intent`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 2. Confirm the card setup
      const cardEl = elements.getElement(CardElement);
      const { setupIntent, error } = await stripe.confirmCardSetup(siData.client_secret, {
        payment_method: { card: cardEl },
      });
      if (error) {
        toast.error(error.message || 'Card setup failed');
        setSaving(false);
        return;
      }

      // 3. Confirm with backend and set as default
      await axios.post(
        `${API}/payments/payment-methods/confirm`,
        { payment_method_id: setupIntent.payment_method, set_as_default: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Card saved!');
      onAdded();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not save card');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3" data-testid="add-card-form">
      <div className="border border-honey/30 rounded-xl p-3 bg-white">
        <CardElement options={CARD_ELEMENT_OPTIONS} />
      </div>
      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={saving || !stripe}
          className="flex-1 bg-[#635bff] text-white hover:bg-[#5146e0] rounded-full gap-2"
          data-testid="save-card-btn"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
          Save Card
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={saving}
          className="rounded-full border-honey/30"
          data-testid="cancel-add-card-btn"
        >
          Cancel
        </Button>
      </div>
    </form>
  );
};

const PaymentMethodList = ({ methods, onRemove, onSetDefault, loading }) => {
  if (methods.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-2" data-testid="no-payment-methods">
        No payment methods saved yet.
      </p>
    );
  }

  return (
    <div className="space-y-2" data-testid="payment-method-list">
      {methods.map((pm) => (
        <div
          key={pm.id}
          className="flex items-center justify-between p-3 rounded-xl border border-honey/20 bg-white"
          data-testid={`payment-method-${pm.id}`}
        >
          <div className="flex items-center gap-3">
            <CreditCard className="w-4 h-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium capitalize">
                {pm.brand} ···· {pm.last4}
                {pm.is_default && (
                  <span className="ml-2 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-semibold">
                    default
                  </span>
                )}
              </p>
              <p className="text-[11px] text-muted-foreground">
                Expires {pm.exp_month}/{pm.exp_year}
              </p>
            </div>
          </div>
          <div className="flex gap-1.5">
            {!pm.is_default && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onSetDefault(pm.id)}
                disabled={loading}
                className="text-xs rounded-full h-7 px-2.5 text-muted-foreground hover:text-foreground"
                data-testid={`set-default-btn-${pm.id}`}
              >
                <Star className="w-3 h-3 mr-1" />
                Set default
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(pm.id)}
              disabled={loading}
              className="text-xs rounded-full h-7 px-2 text-red-400 hover:text-red-600 hover:bg-red-50"
              data-testid={`remove-pm-btn-${pm.id}`}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

const PaymentMethodManagerInner = () => {
  const { token, API, updateUser } = useAuth();
  const [methods, setMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  const fetchMethods = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/payments/payment-methods`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMethods(data.payment_methods || []);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [API, token]);

  useEffect(() => { fetchMethods(); }, [fetchMethods]);

  const handleAdded = async () => {
    setShowAddForm(false);
    await fetchMethods();
    // Refresh user context so has_payment_method updates
    try {
      const { data } = await axios.get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
      if (updateUser) updateUser(data);
    } catch {}
  };

  const handleRemove = async (pmId) => {
    setActionLoading(true);
    try {
      await axios.delete(`${API}/payments/payment-methods/${pmId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Card removed');
      await fetchMethods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not remove card');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSetDefault = async (pmId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/payments/payment-methods/${pmId}/set-default`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Default payment method updated');
      await fetchMethods();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not update default');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">loading payment methods...</span>
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="payment-method-manager">
      <PaymentMethodList
        methods={methods}
        onRemove={handleRemove}
        onSetDefault={handleSetDefault}
        loading={actionLoading}
      />
      {showAddForm ? (
        <AddCardForm onAdded={handleAdded} onCancel={() => setShowAddForm(false)} />
      ) : (
        <Button
          variant="outline"
          onClick={() => setShowAddForm(true)}
          className="rounded-full border-honey/30 gap-2 text-sm"
          data-testid="add-card-open-btn"
        >
          <Plus className="w-4 h-4" />
          Add card
        </Button>
      )}
    </div>
  );
};

const PaymentMethodManager = () => (
  <Elements stripe={stripePromise}>
    <PaymentMethodManagerInner />
  </Elements>
);

export default PaymentMethodManager;
