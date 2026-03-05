import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { ArrowLeft, Calendar, ChevronRight } from 'lucide-react';

const C = {
  bg: '#FAEDC7', textDark: '#2A1A06', textMuted: '#8A6B4A',
  amber: '#996012', amberAccent: '#C8861A', border: 'rgba(200,134,26,0.15)',
};

const WaxReportHistory = () => {
  const { token, API } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/wax-reports/history`, { headers: { Authorization: `Bearer ${token}` }})
      .then(r => setReports(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [API, token]);

  return (
    <div className="min-h-screen pb-24 md:pb-8" style={{ background: C.bg }} data-testid="wax-history-page">
      <div className="max-w-2xl mx-auto px-4 py-8 pt-24">
        <Link to="/collection" className="inline-flex items-center gap-1.5 text-sm mb-6" style={{ color: C.textMuted }} data-testid="wax-history-back">
          <ArrowLeft className="w-4 h-4" /> back to collection
        </Link>
        <h1 className="font-heading text-2xl mb-6" style={{ color: C.textDark }}>past reports</h1>

        {loading ? (
          <div className="space-y-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-20 w-full rounded-2xl" />)}</div>
        ) : reports.length === 0 ? (
          <Card className="p-8 text-center rounded-2xl" style={{ background: '#fff', border: `1px solid ${C.border}` }}>
            <p style={{ color: C.textMuted }}>No reports yet. Keep spinning and check back Sunday!</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {reports.map(r => {
              let weekRange = '';
              try {
                const ws = new Date(r.week_start);
                const we = new Date(r.week_end);
                we.setDate(we.getDate() - 1);
                weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
              } catch { weekRange = ''; }

              return (
                <Link key={r.id} to={`/wax-reports/${r.id}`} data-testid={`wax-history-${r.id}`}>
                  <Card className="p-4 rounded-2xl flex items-center gap-4 transition-all hover:shadow-md"
                    style={{ background: '#fff', border: `1px solid ${C.border}` }}>
                    <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(200,134,26,0.08)' }}>
                      <Calendar className="w-5 h-5" style={{ color: C.amberAccent }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium" style={{ color: C.textDark }}>{weekRange}</p>
                      <p className="text-xs truncate" style={{ color: C.textMuted }}>
                        {r.total_spins} spins · {r.personality?.label?.slice(0, 50)}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 shrink-0" style={{ color: C.textMuted }} />
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default WaxReportHistory;
