import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

export default function ConfirmEmailChangePage() {
  const [searchParams] = useSearchParams();
  const { API } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('No confirmation token found.');
      return;
    }
    axios.get(`${API}/auth/confirm-email-change`, { params: { token } })
      .then(r => {
        setStatus('success');
        setMessage(r.data.message || 'Your email has been updated!');
      })
      .catch(err => {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Could not confirm email change.');
      });
  }, [API, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-honey-soft/30 px-4">
      <Card className="max-w-md w-full border-honey/30">
        <CardContent className="pt-8 pb-6 text-center space-y-4">
          {status === 'loading' && (
            <>
              <Loader2 className="w-10 h-10 mx-auto text-honey animate-spin" />
              <p className="text-muted-foreground">confirming your new email...</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle className="w-10 h-10 mx-auto text-emerald-500" />
              <p className="font-medium text-vinyl-black">{message}</p>
              <Button onClick={() => navigate('/settings')} className="bg-honey text-vinyl-black hover:bg-honey/90" data-testid="email-confirmed-settings-btn">
                go to settings
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="w-10 h-10 mx-auto text-red-500" />
              <p className="font-medium text-vinyl-black">{message}</p>
              <Button onClick={() => navigate('/settings')} variant="outline" data-testid="email-error-settings-btn">
                back to settings
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
