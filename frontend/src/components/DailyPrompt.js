import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Skeleton } from './ui/skeleton';
import { Loader2, Disc, Share2, Send, Download } from 'lucide-react';
import { toast } from 'sonner';
import { trackEvent } from '../utils/analytics';

// ─── Daily Prompt Card (top of Hive feed) ───

export const DailyPromptCard = ({ records, onPostCreated }) => {
  const { user, token, API } = useAuth();
  const [prompt, setPrompt] = useState(null);
  const [hasBuzzedIn, setHasBuzzedIn] = useState(false);
  const [buzzResponse, setBuzzResponse] = useState(null);
  const [streak, setStreak] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchPrompt = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/prompts/today`, { headers: { Authorization: `Bearer ${token}` } });
      setPrompt(r.data.prompt);
      setHasBuzzedIn(r.data.has_buzzed_in);
      setBuzzResponse(r.data.response);
      setStreak(r.data.streak);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  useEffect(() => { fetchPrompt(); }, [fetchPrompt]);

  if (loading) return <Skeleton className="h-32 w-full rounded-xl mb-4" />;
  if (!prompt) return null;

  return (
    <>
      <Card className="mb-4 p-5 border-amber-200/60 bg-gradient-to-br from-amber-50/80 to-orange-50/40 relative overflow-hidden" data-testid="daily-prompt-card">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-100/40 rounded-full -translate-y-8 translate-x-8" />
        <p className="text-[11px] uppercase tracking-widest text-amber-600/70 font-medium mb-2">Daily Prompt</p>
        <p className="font-heading text-xl md:text-2xl text-vinyl-black leading-snug mb-4 italic" data-testid="daily-prompt-text">
          {prompt.text}
        </p>
        <div className="flex items-center justify-between">
          {hasBuzzedIn ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-amber-700 font-medium">buzzed in</span>
              {streak > 0 && <span className="flex items-center gap-1 text-sm text-amber-600 font-bold">🐝 {streak}</span>}
            </div>
          ) : (
            <Button onClick={() => setModalOpen(true)} className="bg-amber-500 hover:bg-amber-600 text-white rounded-full px-6 text-sm font-semibold shadow-sm" data-testid="buzz-in-btn">
              buzz in 🐝
            </Button>
          )}
          {streak > 0 && !hasBuzzedIn && (
            <span className="flex items-center gap-1 text-sm text-amber-600 font-bold">🐝 {streak} day streak</span>
          )}
        </div>
      </Card>

      <BuzzInModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        prompt={prompt}
        records={records}
        onSuccess={(resp) => {
          setHasBuzzedIn(true);
          setBuzzResponse(resp);
          setStreak(resp.streak);
          onPostCreated?.();
        }}
      />
    </>
  );
};

// ─── Buzz-In Modal ───

const BuzzInModal = ({ open, onOpenChange, prompt, records, onSuccess }) => {
  const { user, token, API } = useAuth();
  const [selectedRecordId, setSelectedRecordId] = useState('');
  const [discogsData, setDiscogsData] = useState(null);
  const [loadingDiscogs, setLoadingDiscogs] = useState(false);
  const [caption, setCaption] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [responseData, setResponseData] = useState(null);

  const selectedRecord = records?.find(r => r.id === selectedRecordId);

  // Fetch Discogs data when record selected
  useEffect(() => {
    if (!selectedRecordId || !selectedRecord?.discogs_id) {
      setDiscogsData(null);
      return;
    }
    setLoadingDiscogs(true);
    axios.get(`${API}/prompts/discogs-hires/${selectedRecord.discogs_id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setDiscogsData(r.data))
      .catch(() => setDiscogsData(null))
      .finally(() => setLoadingDiscogs(false));
  }, [selectedRecordId, selectedRecord, API, token]);

  const displayData = discogsData || selectedRecord;
  const coverUrl = discogsData?.cover_url || selectedRecord?.cover_url;
  const labelText = discogsData?.label?.[0] || '';
  const yearText = discogsData?.year || selectedRecord?.year || '';

  const handleSubmit = async (postToHive) => {
    if (!selectedRecordId) { toast.error('select a record first.'); return; }
    setSubmitting(true);
    try {
      const r = await axios.post(`${API}/prompts/buzz-in`, {
        prompt_id: prompt.id,
        record_id: selectedRecordId,
        caption,
        post_to_hive: postToHive,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setResponseData(r.data);
      trackEvent('daily_prompt_answered');
      toast.success(postToHive ? 'Buzzed in & posted to The Hive!' : 'Buzzed in!');
      onSuccess?.(r.data);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  const handleExport = async () => {
    if (!responseData) return;
    setExporting(true);
    try {
      const r = await axios.post(`${API}/prompts/export-card`, { response_id: responseData.id }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });
      const blob = new Blob([r.data], { type: 'image/png' });
      trackEvent('export_card_generated', { card_type: 'daily_prompt' });
      const file = new File([blob], `honeygroove-prompt-${Date.now()}.png`, { type: 'image/png' });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: 'the Honey Groove · Daily Prompt' });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
        toast.success('card downloaded.');
      }
    } catch { toast.error('export failed. try again.'); }
    finally { setExporting(false); }
  };

  const reset = () => {
    setSelectedRecordId(''); setDiscogsData(null); setCaption(''); setResponseData(null);
  };

  return (
    <Dialog open={open} onOpenChange={o => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl">buzz in 🐝</DialogTitle>
          <DialogDescription className="italic text-amber-700">{prompt?.text}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          {!responseData ? (
            <>
              {/* Record selector */}
              <Select value={selectedRecordId} onValueChange={setSelectedRecordId}>
                <SelectTrigger className="border-amber-200" data-testid="buzz-record-select">
                  <SelectValue placeholder="Choose a record from your collection" />
                </SelectTrigger>
                <SelectContent>
                  {records?.map(r => (
                    <SelectItem key={r.id} value={r.id}>{r.artist} · {r.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Live preview */}
              {selectedRecordId && (
                <div className="bg-[#FAF6EE] rounded-xl p-4 space-y-3 border border-amber-100" data-testid="buzz-preview">
                  <p className="text-center italic text-amber-700 text-sm">{prompt?.text}</p>
                  {loadingDiscogs ? (
                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-amber-400" /></div>
                  ) : (
                    <>
                      <div className="flex justify-center">
                        {coverUrl ? (
                          <img src={coverUrl} alt="" className="w-40 h-40 rounded-xl object-cover shadow-md" />
                        ) : (
                          <div className="w-40 h-40 rounded-xl bg-amber-100 flex items-center justify-center"><Disc className="w-10 h-10 text-amber-300" /></div>
                        )}
                      </div>
                      <div className="text-center">
                        <p className="font-heading text-lg">{displayData?.title || 'Unknown'}</p>
                        <p className="text-sm text-muted-foreground">{displayData?.artist || 'Unknown'}</p>
                        {(labelText || yearText) && (
                          <p className="text-xs text-amber-600 italic mt-1">
                            {[labelText, yearText].filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              <Textarea
                placeholder="Add a caption (optional)"
                value={caption} onChange={e => setCaption(e.target.value)}
                className="border-amber-200 resize-none" rows={2}
                data-testid="buzz-caption"
              />

              <div className="grid grid-cols-2 gap-2">
                <Button onClick={() => handleSubmit(false)} disabled={submitting || !selectedRecordId}
                  variant="outline" className="rounded-full border-amber-300 text-amber-700 hover:bg-amber-50" data-testid="buzz-share-only-btn">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Share2 className="w-4 h-4 mr-1" />}
                  share to instagram
                </Button>
                <Button onClick={() => handleSubmit(true)} disabled={submitting || !selectedRecordId}
                  className="rounded-full bg-amber-500 hover:bg-amber-600 text-white" data-testid="buzz-post-hive-btn">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-4 h-4 mr-1" />}
                  post to the hive
                </Button>
              </div>
            </>
          ) : (
            /* Post-submit: export card */
            <div className="text-center space-y-4">
              <div className="bg-amber-50 rounded-xl p-4">
                <p className="text-amber-700 font-medium mb-1">buzzed in! 🐝</p>
                {responseData.streak > 0 && (
                  <p className="flex items-center justify-center gap-1 text-amber-600 font-bold text-lg">
                    🐝 {responseData.streak} day streak
                  </p>
                )}
              </div>
              <Button onClick={handleExport} disabled={exporting}
                className="w-full rounded-full bg-amber-500 hover:bg-amber-600 text-white" data-testid="buzz-export-btn">
                {exporting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
                save & share card
              </Button>
              <Button variant="ghost" onClick={() => onOpenChange(false)} className="w-full text-muted-foreground">
                done
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ─── Streak Badge (for ProfilePage) ───

export const StreakBadge = ({ username }) => {
  const { API } = useAuth();
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    if (!username) return;
    axios.get(`${API}/prompts/streak/${username}`)
      .then(r => setStreak(r.data.streak))
      .catch(() => {});
  }, [API, username]);

  if (streak <= 0) return null;
  return (
    <div className="flex items-center gap-1.5 text-amber-600 font-bold text-sm" data-testid="profile-streak-badge">
      🐝 {streak} day streak
    </div>
  );
};

export default DailyPromptCard;
