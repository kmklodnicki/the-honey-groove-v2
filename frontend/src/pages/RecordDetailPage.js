import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Play, ArrowLeft, Share2, Calendar, User, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

const RecordDetailPage = () => {
  const { recordId } = useParams();
  const { user, token, API } = useAuth();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [spinning, setSpinning] = useState(false);

  useEffect(() => {
    fetchRecord();
  }, [recordId]);

  const fetchRecord = async () => {
    try {
      const response = await axios.get(`${API}/records/${recordId}`);
      setRecord(response.data);
    } catch (error) {
      console.error('Failed to fetch record:', error);
      toast.error('Record not found');
      navigate('/collection');
    } finally {
      setLoading(false);
    }
  };

  const handleLogSpin = async () => {
    if (!token) {
      toast.error('Please sign in to log spins');
      return;
    }

    setSpinning(true);
    try {
      await axios.post(`${API}/spins`, 
        { record_id: recordId },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      toast.success(`Now spinning: ${record.title}`);
      fetchRecord();
    } catch (error) {
      console.error('Failed to log spin:', error);
      toast.error(error.response?.data?.detail || 'Failed to log spin');
    } finally {
      setSpinning(false);
    }
  };

  const handleShare = async () => {
    if (!token) {
      toast.error('Please sign in to share');
      return;
    }

    try {
      const response = await axios.post(`${API}/share/generate`, 
        { graphic_type: 'now_spinning', record_id: recordId },
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `now_spinning_${record.artist}_${record.title}.png`.replace(/[^a-z0-9_.-]/gi, '_');
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Now Spinning image downloaded!');
    } catch (error) {
      console.error('Share error:', error);
      toast.error('Failed to generate share image');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to remove this record from your collection?')) return;

    try {
      await axios.delete(`${API}/records/${recordId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Record removed from collection');
      navigate('/collection');
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to remove record');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <div className="flex gap-8">
          <Skeleton className="w-80 h-80 rounded-xl" />
          <div className="flex-1 space-y-4">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-4 w-1/4" />
          </div>
        </div>
      </div>
    );
  }

  if (!record) return null;

  const isOwner = user?.id === record.user_id;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-6 gap-2"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Album Cover */}
        <div className="md:w-80 flex-shrink-0">
          <div className={`aspect-square rounded-xl overflow-hidden shadow-vinyl bg-vinyl-black ${spinning ? 'animate-spin-slow' : ''}`}>
            {record.cover_url ? (
              <img 
                src={record.cover_url} 
                alt={record.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Disc className="w-24 h-24 text-honey" />
              </div>
            )}
          </div>
        </div>

        {/* Record Info */}
        <div className="flex-1">
          <h1 className="font-heading text-3xl md:text-4xl text-vinyl-black mb-2">{record.title}</h1>
          <p className="text-xl text-muted-foreground mb-4">{record.artist}</p>

          <div className="flex flex-wrap gap-3 mb-6">
            {record.year && (
              <span className="inline-flex items-center gap-1 text-sm bg-honey/20 px-3 py-1 rounded-full">
                <Calendar className="w-4 h-4" />
                {record.year}
              </span>
            )}
            {record.format && (
              <span className="text-sm bg-vinyl-black text-white px-3 py-1 rounded-full">
                {record.format}
              </span>
            )}
            <span className="inline-flex items-center gap-1 text-sm bg-honey/20 px-3 py-1 rounded-full">
              <Play className="w-4 h-4" />
              {record.spin_count} {record.spin_count === 1 ? 'spin' : 'spins'}
            </span>
          </div>

          {record.notes && (
            <Card className="p-4 mb-6 border-honey/30 bg-honey/5">
              <h3 className="text-sm font-medium mb-2">Notes</h3>
              <p className="text-muted-foreground">{record.notes}</p>
            </Card>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {isOwner && (
              <Button
                onClick={handleLogSpin}
                disabled={spinning}
                className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2"
                data-testid="spin-btn"
              >
                <Play className="w-4 h-4" />
                {spinning ? 'Spinning...' : 'Log Spin'}
              </Button>
            )}
            
            {token && (
              <Button
                variant="outline"
                onClick={handleShare}
                className="gap-2 rounded-full"
                data-testid="share-btn"
              >
                <Share2 className="w-4 h-4" />
                Share
              </Button>
            )}

            {isOwner && (
              <Button
                variant="ghost"
                onClick={handleDelete}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 gap-2"
                data-testid="delete-btn"
              >
                <Trash2 className="w-4 h-4" />
                Remove
              </Button>
            )}
          </div>

          {/* Discogs Link */}
          {record.discogs_id && (
            <a 
              href={`https://www.discogs.com/release/${record.discogs_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-6 text-sm text-muted-foreground hover:text-honey-amber transition-colors"
            >
              View on Discogs →
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecordDetailPage;
