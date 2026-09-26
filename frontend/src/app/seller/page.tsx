'use client';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import AppShell from '../../components/AppShell';
import StatCard from '../../components/StatCard';
import DemandRadar from '../../components/DemandRadar';
import { acceptOffer, applySeller, getMyListings, getMySeller, getOffersInbox, getOffersSent, getSellerAnalytics, removeListing, rejectOffer, withdrawOffer, type Listing, type Offer, type Seller } from '../../lib/api';

export default function Seller() {
  const search = useSearchParams();
  const tab = search.get('tab') === 'offers' ? 'offers' : 'overview';
  const offerView = search.get('view') === 'sent' ? 'sent' : 'inbox';
  const [seller, setSeller] = useState<Seller | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [analytics, setAnalytics] = useState<{ estimated_sales: number; active_listings: number; offers: number; views: number; saves: number; shares: number } | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [error, setError] = useState('');
  const [busyOffer, setBusyOffer] = useState<number | null>(null);
  const [sentOffers, setSentOffers] = useState<Offer[]>([]);

  const load = async () => {
    try {
      const [l, a, o, s] = await Promise.all([getMyListings(), getSellerAnalytics(), getOffersInbox(), getOffersSent()]);
      setListings(l); setAnalytics(a); setOffers(o); setSentOffers(s);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load seller studio'); }
  };

  useEffect(() => {
    getMySeller().then(setSeller).catch(async () => {
      try { setSeller(await applySeller({ display_name: 'CampusCart Seller', bio: 'Student seller on CampusCart.' })); }
      catch (e) { setError(e instanceof Error ? e.message : 'Create your seller profile before listing'); }
    });
  }, []);

  useEffect(() => { if (seller) load(); }, [seller]);

  const decideOffer = async (offer: Offer, action: 'accept' | 'reject') => {
    setBusyOffer(offer.id); setError('');
    try {
      if (action === 'accept') await acceptOffer(offer.id); else await rejectOffer(offer.id);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to update offer'); }
    finally { setBusyOffer(null); }
  };

  const remove = async (listing: Listing) => {
    if (!window.confirm(`Remove "${listing.title}" from the marketplace?`)) return;
    try { await removeListing(listing.id); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to remove listing'); }
  };

  return <AppShell active={tab === 'offers' ? 'Offers' : 'My Listings'}>
    <div className="page-header"><div><div className="eyebrow">SELLER STUDIO</div><h1>{tab === 'offers' ? 'Offers' : 'Your selling space'}</h1></div><Link className="btn btn-primary" href="/seller/new">＋ Create listing</Link></div>
    {error && <div className="error-box" style={{ marginBottom: 14 }}>{error}</div>}

    {tab === 'overview' ? <>
      <div className="stat-grid"><StatCard value={`₹${Number(analytics?.estimated_sales || 0).toLocaleString('en-IN')}`} label="Estimated listing value" accent="green"/><StatCard value={String(analytics?.active_listings || 0)} label="Active listings"/><StatCard value={String(analytics?.offers || offers.length || 0)} label="Offers" accent="violet"/><StatCard value={String(analytics?.saves || 0)} label="Saves"/></div>
      <div className="dashboard-grid"><section className="panel"><div className="panel-head"><h2>Your listings</h2><Link href="/seller/new">New listing →</Link></div>{listings.slice(0, 8).map((p) => <div key={p.id} className="seller-list-row"><img src={p.images?.[0]?.url || '/products/math.svg'} alt=""/><div><strong>{p.title}</strong><div className="muted small">₹{Number(p.price).toLocaleString('en-IN')} · {p.views} views · {p.favorites} saves · {p.share_count} shares</div></div><div className="seller-row-actions"><span className="verify">{p.status}</span><Link className="btn btn-ghost" href={`/seller/edit/${p.id}`}>Edit</Link><button className="btn btn-ghost" onClick={() => remove(p)}>Remove</button></div></div>)}{!listings.length && <div className="empty-state"><strong>No listings yet</strong><span>Create your first campus listing.</span></div>}</section><section className="panel"><div className="panel-head"><h2>Campus demand</h2><Link href="/demand">Open radar →</Link></div><DemandRadar compact/><div className="success-box">Use demand signals before choosing what to list next.</div></section></div>
      <section className="panel" style={{ marginTop: 16 }}><div className="panel-head"><h2>Latest offers</h2><Link href="/seller?tab=offers">Manage all →</Link></div>{offers.slice(0, 5).map((o) => <div key={o.id} className="offer-row"><div><strong>{o.listing_title || `Listing #${o.listing_id}`}</strong><span>{o.buyer_name || 'Buyer'} · ₹{Number(o.amount).toLocaleString('en-IN')}</span></div><span className={`transaction-status ${o.status === 'accepted' ? 'completed' : 'active'}`}>{o.status}</span></div>)}</section>
    </> : <section className="panel"><div className="offer-tabbar"><Link className="category-chip" href="/seller">Overview</Link><Link className={offerView === 'inbox' ? 'category-chip active' : 'category-chip'} href="/seller?tab=offers&view=inbox">Offers received ({offers.length})</Link><Link className={offerView === 'sent' ? 'category-chip active' : 'category-chip'} href="/seller?tab=offers&view=sent">Offers sent ({sentOffers.length})</Link></div>{offerView === 'inbox' ? offers.map((o) => <div key={o.id} className="offer-management-row"><div><strong>{o.listing_title || `Listing #${o.listing_id}`}</strong><p>{o.buyer_name || 'Buyer'} offered <strong>₹{Number(o.amount).toLocaleString('en-IN')}</strong></p><span>{o.message || 'No message'} · {new Date(o.created_at).toLocaleString('en-IN')}</span></div><div className="offer-actions">{o.status === 'pending' ? <><button className="btn btn-primary" disabled={busyOffer === o.id} onClick={() => decideOffer(o, 'accept')}>{busyOffer === o.id ? 'Working...' : 'Accept'}</button><button className="btn btn-ghost" disabled={busyOffer === o.id} onClick={() => decideOffer(o, 'reject')}>Reject</button></> : <span className={`transaction-status ${o.status === 'accepted' ? 'completed' : 'active'}`}>{o.status}</span>}</div></div>) : sentOffers.map((o) => <div key={o.id} className="offer-management-row"><div><strong>{o.listing_title || `Listing #${o.listing_id}`}</strong><p>Sent ₹{Number(o.amount).toLocaleString('en-IN')} to {o.seller_name || 'Seller'}</p><span>{o.message || 'No message'} · {new Date(o.created_at).toLocaleString('en-IN')}</span></div><div className="offer-actions">{o.status === 'pending' ? <button className="btn btn-ghost" disabled={busyOffer === o.id} onClick={async () => { setBusyOffer(o.id); try { await withdrawOffer(o.id); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to withdraw offer'); } finally { setBusyOffer(null); } }}>{busyOffer === o.id ? 'Withdrawing...' : 'Withdraw'}</button> : <span className={`transaction-status ${o.status === 'accepted' ? 'completed' : 'active'}`}>{o.status}</span>}</div></div>)}{offerView === 'inbox' && !offers.length && <div className="empty-state"><strong>No offers received yet</strong><span>Buyer offers will appear here.</span></div>}{offerView === 'sent' && !sentOffers.length && <div className="empty-state"><strong>No offers sent yet</strong><span>Open a listing and make an offer to see it here.</span></div>}</section>}
  </AppShell>;
}
