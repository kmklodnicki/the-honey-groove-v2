/**
 * WaxReportPin — shows the user's latest Wax Report as a pinned card on their profile.
 * Extracted from ProfilePage.js for reusability.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Card } from './ui/card';
import { Disc } from 'lucide-react';

const WaxReportPin = ({ username, API, token }) => {
  const [report, setReport] = useState(null);
  useEffect(() => {
    axios.get(`${API}/wax-reports/latest/${username}`)
      .then(r => setReport(r.data))
      .catch(() => {});
  }, [API, username]);

  if (!report) return null;

  let weekRange = '';
  try {
    const ws = new Date(report.week_start);
    const we = new Date(report.week_end);
    we.setDate(we.getDate() - 1);
    weekRange = `${ws.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} · ${we.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { weekRange = ''; }

  return (
    <Link to={`/wax-reports/${report.id}`} className="block mb-4" data-testid="profile-wax-pin">
      <Card className="p-4 rounded-2xl shadow-sm hover:shadow-md transition-all" style={{ background: '#FAEDC7', border: '1px solid rgba(200,134,26,0.15)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(200,134,26,0.08)' }}>
            <Disc className="w-4 h-4" style={{ color: '#C8861A' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-heading" style={{ color: '#2A1A06' }}>your week in wax</p>
            <p className="text-[11px] truncate" style={{ color: '#8A6B4A' }}>
              {weekRange} · {report.total_spins} spins · {report.personality?.label?.slice(0, 40)}...
            </p>
          </div>
          <span className="text-[11px] shrink-0" style={{ color: '#C8861A' }}>View &rarr;</span>
        </div>
      </Card>
    </Link>
  );
};

export default WaxReportPin;
