'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import AppShell from '../../../components/AppShell';
import TransactionHandoff from '../../../components/TransactionHandoff';
import PickupScheduler from '../../../components/PickupScheduler';
import ReviewForm from '../../../components/ReviewForm';
import { cancelTransaction, getCampus, getListing, getTransaction, refundPayment, type Campus, type Listing, type Transaction } from '../../../lib/api';

const labels: [string, string][] = [
  ['awaiting_payment', 'Offer accepted'],
  ['swap_accepted', 'Swap accepted'],
  ['paid', 'Payment received'],
  ['pickup_scheduled', 'Pickup scheduled'],
  ['waiting_handoff', 'Waiting for handoff'],
  ['completed', 'Completed'],
];

export default function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const [tx, setTx] = useState<Transaction | null>(null);
  const [listing, setListing] = useState<Listing | null>(null);
  const [campus, setCampus] = useState<Campus | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const nextTx = await getTransaction(Number(id));
      const nextListing = await getListing(nextTx.listing_id);
      const nextCampus = await getCampus(nextListing.campus_slug);
      setTx(nextTx);
      setListing(nextListing);
      setCampus(nextCampus);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load transaction');
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const cancel = async () => {
    if (!tx || !window.confirm('Cancel this transaction?')) return;
    setBusy(true);
    setError('');
    try {
      await cancelTransaction(tx.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to cancel transaction');
    } finally {
      setBusy(false);
    }
  };

  const refundAndCancel = async () => {
    if (!tx?.payment_id || !window.confirm('Refund the payment and cancel this transaction?')) return;
    setBusy(true);
    setError('');
    try {
      await refundPayment(tx.payment_id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to refund this transaction');
    } finally {
      setBusy(false);
    }
  };

  if (error) return <AppShell active="Transactions"><div className="error-box">{error}</div></AppShell>;
  if (!tx || !listing) return <AppShell active="Transactions"><div className="muted">Loading transaction...</div></AppShell>;

  const currentIndex = Math.max(0, labels.findIndex(([status]) => status === tx.status));
  const isSwap = Boolean(tx.swap_offer_id);
  const canPay = tx.status === 'awaiting_payment' && tx.viewer_role === 'buyer' && !isSwap;
  const canCancel = tx.status === 'awaiting_payment' && Boolean(tx.viewer_role);
  const canRefund = tx.viewer_role === 'buyer' && Boolean(tx.payment_id) && tx.payment_status === 'captured' && !['completed', 'cancelled'].includes(tx.status);

  return (
    <AppShell active="Transactions">
      <div className="page-header">
        <div>
          <Link href="/transactions" className="muted small">← Back to transactions</Link>
          <div className="eyebrow transaction-eyebrow">TRANSACTION #{tx.id}{isSwap ? ' · SWAP' : ''}</div>
          <h1>{listing.title}</h1>
        </div>
        <div className="page-actions">
          <span className="verified-badge">{isSwap ? 'Swap exchange · no payment' : `₹${Number(tx.agreed_price).toLocaleString('en-IN')}`} · {tx.status.replaceAll('_', ' ')}</span>
          {canCancel && <button className="btn btn-ghost" disabled={busy} onClick={cancel}>{busy ? 'Cancelling...' : 'Cancel transaction'}</button>}
          {canRefund && <button className="btn btn-ghost" disabled={busy} onClick={refundAndCancel}>{busy ? 'Refunding...' : 'Refund & cancel'}</button>}
        </div>
      </div>

      <div className="transaction-summary">
        <div className="transaction-summary-card">
          <img src={listing.images?.[0]?.url || '/products/math.svg'} alt={listing.title} />
          <div>
            <div className="eyebrow">{isSwap ? 'SWAP' : tx.viewer_role === 'seller' ? 'SALE' : 'PURCHASE'}</div>
            <h2>{listing.title}</h2>
            <p className="muted small">{listing.condition} · {listing.category} · {listing.campus_slug}</p>
          </div>
          <div className="transaction-summary-price">
            <span>Total</span>
            <strong>{isSwap ? '₹0' : `₹${Number(tx.agreed_price).toLocaleString('en-IN')}`}</strong>
            <small>{isSwap ? 'No payment required' : tx.paid_at ? 'Paid via UPI' : 'Payment pending'}</small>
          </div>
        </div>
      </div>

      <div className="transaction-page">
        <section className="panel transaction-timeline-panel">
          <div className="panel-head">
            <div><div className="eyebrow">TRANSACTION STATUS</div><h2>{isSwap ? 'Swap progress' : 'Purchase progress'}</h2></div>
            <span className={`transaction-status ${tx.status === 'completed' ? 'completed' : 'active'}`}>{tx.status.replaceAll('_', ' ')}</span>
          </div>
          {isSwap && <div className="success-box" style={{ marginBottom: 16 }}>The swap has been accepted. No payment is required; schedule a pickup to continue.</div>}
          <div className="timeline">
            {labels.map(([status, label], index) => (
              <div key={status} className={index < currentIndex ? 'timeline-item done' : index === currentIndex ? 'timeline-item current' : 'timeline-item'}>
                <strong>{label}</strong>
                <span>
                  {status === 'pickup_scheduled' && tx.pickup_date ? `${tx.pickup_date} · ${tx.pickup_time || ''}`
                    : status === 'paid' && tx.paid_at ? new Date(tx.paid_at).toLocaleString('en-IN')
                      : status === 'completed' && tx.completed_at ? new Date(tx.completed_at).toLocaleString('en-IN')
                        : status === 'awaiting_payment' && canPay ? 'Complete payment to unlock pickup scheduling.'
                          : status === 'swap_accepted' && isSwap ? 'Choose a campus pickup point or saved address.'
                            : 'State recorded in CampusCart'}
                </span>
              </div>
            ))}
          </div>
          {canPay && <Link className="btn btn-primary" style={{ marginTop: 18 }} href={`/checkout/${tx.id}`}>Continue to payment →</Link>}
        </section>

        <aside className="transaction-side-stack">
          <section className="panel">
            <div className="eyebrow">PICKUP DETAILS</div>
            <h2 className="transaction-side-title">{tx.pickup_address || (tx.pickup_location_id ? campus?.pickup_locations?.find(point => point.id === tx.pickup_location_id)?.address : '') || 'Pickup not scheduled'}</h2>
            <p className="muted small">
              {tx.pickup_landmark || campus?.pickup_locations?.find(point => point.id === tx.pickup_location_id)?.landmark || (isSwap ? 'Choose a pickup point for the exchange.' : 'Choose a pickup point after payment.')}
              <br />{campus?.city}, {campus?.state}
            </p>
            <div className="pickup-meta"><div><span>Date</span><strong>{tx.pickup_date || '—'}</strong></div><div><span>Time</span><strong>{tx.pickup_time?.slice(0, 5) || '—'}</strong></div></div>
            {tx.viewer_role === 'buyer' && tx.handoff_code && (tx.status === 'pickup_scheduled' || tx.status === 'waiting_handoff') && (
              <div className="handoff buyer-code-card"><small>YOUR HANDOFF CODE</small><div className="handoff-code">{tx.handoff_code.split('').map((digit, index) => <span key={`${digit}-${index}`}>{digit}</span>)}</div><p className="muted small">Share this 4-digit code with the seller at pickup.</p></div>
            )}
            <PickupScheduler transaction={tx} campus={campus} onUpdate={setTx} />
            {(tx.status === 'pickup_scheduled' || tx.status === 'waiting_handoff') && <TransactionHandoff transaction={tx} onUpdate={setTx} />}
          </section>

          <section className="panel">
            <div className="eyebrow">SELLER</div>
            <div className="transaction-seller"><div className="seller-avatar">{listing.seller.display_name.charAt(0)}</div><div><strong>{listing.seller.display_name}</strong><span>★ {Number(listing.seller.reputation_score).toFixed(1)} · {listing.seller.completed_orders} completed transactions</span></div></div>
            <div className="transaction-side-actions"><Link href={`/messages?listing=${listing.id}`} className="btn btn-ghost full">Message seller</Link></div>
          </section>

          {canRefund && <section className="panel"><div className="eyebrow">PAYMENT</div><h3 className="transaction-info-title">Payment is captured</h3><p className="transaction-info-copy muted small">To cancel a paid transaction, use the refund flow first.</p><button className="btn btn-primary full" style={{ marginTop: 12 }} disabled={busy} onClick={refundAndCancel}>{busy ? 'Refunding...' : 'Refund payment & cancel'}</button></section>}
          {tx.status === 'completed' && <section className="panel"><ReviewForm transactionId={tx.id} /></section>}
        </aside>
      </div>
    </AppShell>
  );
}
