'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import AppShell from '../../components/AppShell';
import { acceptSwap, getCampusSlug, getListing, getMyListings, getSwapCycles, getSwapInbox, getSwapMatches, getSwapSent, proposeSwap, rejectSwap, type Listing, type SwapOffer } from '../../lib/api';

type SwapWithTransaction = SwapOffer & { transaction_id?: number | null };

export default function SwapPage() {
  const query = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const [mine, setMine] = useState<Listing[]>([]);
  const [have, setHave] = useState(0);
  const [matches, setMatches] = useState<{ listing_id: number; title: string; seller_id: number; score: number }[]>([]);
  const [cycles, setCycles] = useState<{ path: number[]; score: number }[]>([]);
  const [linked, setLinked] = useState<Listing | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState<number | null>(null);
  const [inbox, setInbox] = useState<SwapWithTransaction[]>([]);
  const [outbox, setOutbox] = useState<SwapWithTransaction[]>([]);
  const [busy, setBusy] = useState<number | null>(null);

  const load = async () => {
    try {
      const [m, i, o, c] = await Promise.all([getMyListings(), getSwapInbox(), getSwapSent(), getSwapCycles(getCampusSlug())]);
      setMine(m);
      setInbox(i);
      setOutbox(o);
      setCycles(c);
      setHave(Number(query.get('listing')) || m[0]?.id || 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load swap data');
    }
  };

  useEffect(() => {
    void load();
    const linkedId = Number(query.get('listing') || 0);
    if (linkedId) getListing(linkedId).then(setLinked).catch(() => {});
  }, []);

  const find = async () => {
    if (!have) return;
    try { setMatches(await getSwapMatches(have)); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to find matches'); }
  };

  const propose = async (id: number) => {
    try { await proposeSwap({ offered_listing_id: have, requested_listing_id: id, message }); setSent(id); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to propose swap'); }
  };

  const decide = async (id: number, action: 'accept' | 'reject') => {
    setBusy(id);
    try { if (action === 'accept') await acceptSwap(id); else await rejectSwap(id); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to update swap'); }
    finally { setBusy(null); }
  };

  const card = (swap: SwapWithTransaction, incoming: boolean) => (
    <div className="offer-management-row" key={swap.id}>
      <div>
        <strong>{swap.offered_listing_title} ⇄ {swap.requested_listing_title}</strong>
        <p>{incoming ? (swap.proposer_name || 'Student') : (swap.receiver_name || 'Student')} · {swap.compatibility}% compatible</p>
        <span>{swap.message || 'No message'}</span>
        {swap.status === 'accepted' && swap.transaction_id && <div style={{ marginTop: 7 }}><Link href={`/transactions/${swap.transaction_id}`} className="card-link">View exchange transaction →</Link></div>}
      </div>
      <div className="offer-actions">
        {incoming && swap.status === 'pending' ? <>
          <button className="btn btn-primary" disabled={busy === swap.id} onClick={() => decide(swap.id, 'accept')}>Accept</button>
          <button className="btn btn-ghost" disabled={busy === swap.id} onClick={() => decide(swap.id, 'reject')}>Reject</button>
        </> : <span className={`transaction-status ${swap.status === 'accepted' ? 'completed' : 'active'}`}>{swap.status}</span>}
      </div>
    </div>
  );

  return (
    <AppShell active="Smart Swap">
      <div className="page-header"><div><div className="eyebrow">CAMPUS EXCHANGE</div><h1>Smart Swap</h1><p className="muted" style={{ fontSize: 13, marginTop: 4 }}>Trade an item you have for something another student has.</p></div></div>
      <section className="swap-hero">
        <div className="eyebrow">FIND A MATCH</div><h2 style={{ fontSize: 26, letterSpacing: '-.04em', margin: '4px 0' }}>What do you have — and what do you want?</h2>
        {linked && <div className="success-box" style={{ marginBottom: 14 }}>Starting from <strong>{linked.title}</strong>.</div>}
        <div className="swap-inputs"><label className="swap-box"><span>I have</span><select value={have} onChange={e => setHave(Number(e.target.value))}>{mine.map(x => <option key={x.id} value={x.id}>{x.title}</option>)}</select></label><div className="swap-arrow">⇄</div><div className="swap-box"><span>I want</span><strong>Find a compatible campus listing</strong></div></div>
        <label style={{ display: 'block', marginTop: 12 }}>Message to the other student<textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="Why would this swap work for you?" /></label>
        <button className="btn btn-primary" onClick={find} disabled={!have}>Find matches →</button>
        {error && <div className="error-box">{error}</div>}
      </section>
      {matches.length > 0 && <section style={{ marginTop: 18 }}><div className="panel-head"><h2>{matches.length} possible matches</h2><span className="verified-badge">Smart match engine</span></div><div className="match-grid">{matches.map(m => <div className="match-card" key={m.listing_id}><div className="match-top"><strong>{m.title}</strong><span className="match-score">{m.score}%</span></div><p>Compatible with <strong>{mine.find(x => x.id === have)?.title}</strong>.</p>{sent && sent === m.listing_id ? <div className="success-box">Swap proposal sent ✓</div> : <button className="btn btn-primary full" onClick={() => propose(m.listing_id)}>Propose Swap</button>}</div>)}</div></section>}
      <section className="dashboard-grid" style={{ marginTop: 18 }}>
        <div className="panel"><div className="panel-head"><h2>Incoming requests</h2><span className="muted small">Respond to proposals</span></div>{inbox.map(s => card(s, true))}{!inbox.length && <div className="empty-state"><strong>No incoming proposals</strong><span>New swap requests will appear here.</span></div>}</div>
        <div className="panel"><div className="panel-head"><h2>Sent proposals</h2><span className="muted small">Track your requests</span></div>{outbox.map(s => card(s, false))}{!outbox.length && <div className="empty-state"><strong>No proposals yet</strong><span>Find a match above to propose your first swap.</span></div>}</div>
      </section>
      <section className="panel" style={{ marginTop: 18 }}><div className="panel-head"><h2>Swap cycles</h2><span className="muted small">Multi-person possibilities from campus inventory</span></div>{cycles.length ? cycles.map((c, i) => <div className="swap-cycle-row" key={i}><span>Cycle {i + 1}</span><strong>{c.path.map(id => `#${id}`).join(' → ')}</strong><span>{c.score}%</span></div>) : <div className="empty-state"><strong>No swap cycles yet</strong><span>More active listings create more possible exchange paths.</span></div>}</section>
    </AppShell>
  );
}
