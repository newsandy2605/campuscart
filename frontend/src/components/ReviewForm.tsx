'use client';
import { useState } from 'react';
import { reviewTransaction } from '../lib/api';

export default function ReviewForm({ transactionId, onDone }: { transactionId: number; onDone?: () => void }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setBusy(true); setError('');
    try {
      await reviewTransaction(transactionId, rating, comment);
      setDone(true);
      onDone?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to submit review');
    } finally { setBusy(false); }
  };

  if (done) return <div className="success-box">Thanks. Your review has been recorded.</div>;

  return <div className="review-form">
    <div className="eyebrow">TRUST</div>
    <h3>How was the transaction?</h3>
    <div className="review-stars">{[1,2,3,4,5].map((x) => <button type="button" key={x} className={x <= rating ? 'star active' : 'star'} onClick={() => setRating(x)} aria-label={`${x} stars`}>★</button>)}</div>
    <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Optional comment about the buyer/seller..." />
    {error && <div className="error-box">{error}</div>}
    <button className="btn btn-primary" onClick={submit} disabled={busy}>{busy ? 'Submitting...' : 'Submit review'}</button>
  </div>;
}
