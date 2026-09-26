'use client';

import { useEffect, useState } from 'react';
import AppShell from '../../../components/AppShell';
import { getReports, moderateListing, resolveReport } from '../../../lib/api';

type Report = {
  id: number;
  reporter_id: number;
  target_type: string;
  target_id: number;
  reason: string;
  notes: string;
  status: string;
  created_at: string;
  resolved_at?: string | null;
};

export default function AdminReports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<number | null>(null);

  const load = async () => {
    try {
      setReports(await getReports());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load reports');
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const act = async (id: number, status: 'resolved' | 'dismissed') => {
    setBusy(id);
    try {
      await resolveReport(id, status);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to resolve report');
    } finally {
      setBusy(null);
    }
  };

  const remove = async (id: number) => {
    if (!window.confirm('Remove this listing from the marketplace?')) return;
    setBusy(id);
    try {
      await moderateListing(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to remove listing');
    } finally {
      setBusy(null);
    }
  };

  return (
    <AppShell active="Admin">
      <div className="page-header">
        <div>
          <div className="eyebrow">MODERATION</div>
          <h1>Reports</h1>
          <p className="muted small">Review user reports and record the moderation outcome.</p>
        </div>
      </div>
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        {reports.map((report) => (
          <div className="offer-management-row" key={report.id}>
            <div>
              <strong>Report #{report.id} · {report.target_type} #{report.target_id}</strong>
              <p>{report.reason}</p>
              <span>{report.notes || 'No notes provided'} · {new Date(report.created_at).toLocaleString('en-IN')}</span>
              <div className="muted small" style={{ marginTop: 5 }}>Status: {report.status}</div>
            </div>
            <div className="offer-actions">
              {report.status === 'open' && <>
                <button className="btn btn-ghost" disabled={busy === report.id} onClick={() => act(report.id, 'dismissed')}>Dismiss</button>
                <button className="btn btn-primary" disabled={busy === report.id} onClick={() => act(report.id, 'resolved')}>Resolve</button>
                {report.target_type === 'listing' && <button className="btn btn-ghost" disabled={busy === report.id} onClick={() => remove(report.target_id)}>Remove listing</button>}
              </>}
            </div>
          </div>
        ))}
        {!reports.length && <div className="empty-state"><strong>No reports</strong><span>Reported content will appear here.</span></div>}
      </section>
    </AppShell>
  );
}
