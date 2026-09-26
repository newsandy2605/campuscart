'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import AppShell from '../../../components/AppShell';
import { getListing, getTransaction, type Listing, type Transaction } from '../../../lib/api';

export default function Checkout() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [tx, setTx] = useState<Transaction | null>(null);
  const [listing, setListing] = useState<Listing | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { const id = Number(params.id); getTransaction(id).then(async (t) => { setTx(t); setListing(await getListing(t.listing_id)); }).catch((e) => setError(e instanceof Error ? e.message : 'Unable to load checkout')); }, [params.id]);
  return <AppShell active="Transactions"><div className="page-header"><div><div className="eyebrow">CHECKOUT</div><h1>Review & pay</h1></div></div>{error ? <div className="error-box">{error}</div> : tx && listing ? <div className="checkout-grid"><section className="checkout-card"><div className="checkout-item"><img src={listing.images?.[0]?.url || '/products/math.svg'} alt=""/><div><strong>{listing.title}</strong><p className="muted small">{listing.condition} · {listing.category}</p><span className="verify">✓ {listing.seller.display_name} · verified seller</span></div><strong style={{ marginLeft: 'auto' }}>₹{Number(tx.agreed_price).toLocaleString('en-IN')}</strong></div><div className="checkout-line"><span>Pickup</span><strong>{tx.pickup_address || 'Choose after payment'}</strong></div><div className="checkout-line"><span>Landmark</span><strong>{tx.pickup_landmark || 'Choose a pickup point after payment'}</strong></div><div className="checkout-line"><span>Payment</span><strong>UPI</strong></div></section><aside className="checkout-card"><div className="upi-method"><div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}><div><strong>Pay with UPI</strong><p className="muted small">Secure checkout. Your payment status is confirmed by the payment service.</p></div><span className="upi-logo">UPI</span></div></div><div className="checkout-line"><span>Item</span><strong>₹{Number(tx.agreed_price).toLocaleString('en-IN')}</strong></div><div className="checkout-line"><span>CampusCart fee</span><strong>₹0</strong></div><div className="checkout-line checkout-total"><span>Total</span><strong>₹{Number(tx.agreed_price).toLocaleString('en-IN')}</strong></div>{tx.status === 'awaiting_payment' ? <button className="btn btn-primary full" style={{ marginTop: 14 }} onClick={() => router.push(`/payment/${tx.id}`)}>Continue to Payment →</button> : <div className="success-box" style={{ marginTop: 14 }}>This transaction is currently <strong>{tx.status.replaceAll('_', ' ')}</strong>.</div>}</aside></div> : <div className="muted">Loading checkout...</div>}</AppShell>;
}
