'use client';
import Link from 'next/link';
import { useState } from 'react';
import OfferModal from './OfferModal';
import { createConversation, favoriteListing, reportTarget, shareListing, type Listing } from '../lib/api';
import { useRouter } from 'next/navigation';

export default function ListingDetailClient({ listing }: { listing: Listing }) {
  const router = useRouter();
  const [offerOpen, setOfferOpen] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const [reported, setReported] = useState(false);
  const image = listing.images?.[0]?.url || '/products/math.svg';
  const unavailable = listing.status !== 'active';

  const message = async () => {
    try {
      const c = await createConversation(listing.id);
      router.push(`/messages?conversation=${c.id}`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to start conversation'); }
  };

  const save = async () => {
    try { const r = await favoriteListing(listing.id); setSaved(r.favorite); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to save listing'); }
  };

  const share = async () => {
    try {
      const r = await shareListing(listing.id);
      window.open(r.whatsapp_url, '_blank', 'noopener,noreferrer');
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to share'); }
  };

  const report = async () => {
    try {
      await reportTarget({ target_type: 'listing', target_id: listing.id, reason: 'listing_report', notes: 'Reported from listing detail.' });
      setReported(true);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to report listing'); }
  };

  return <>
    <div className="page-header"><div><Link href="/marketplace" className="muted small">← Back to marketplace</Link></div><div className="page-actions"><button className="btn btn-ghost" onClick={share}>↗ Share</button><button className="btn btn-ghost" onClick={report} disabled={reported}>{reported ? 'Reported' : 'Report'}</button></div></div>
    <div className="detail-grid">
      <div className="detail-gallery"><div className="thumbs">{(listing.images.length ? listing.images : [{ url: image, alt: listing.title }]).slice(0, 4).map((x, i) => <div className="thumb" key={i}><img src={x.url} alt={x.alt || listing.title} /></div>)}</div><div className="main-product-image"><img src={image} alt={listing.title} /></div></div>
      <div className="detail-copy">
        <div className="verified-badge">✓ {listing.seller.verified ? 'Campus verified seller' : 'Campus seller'}</div>
        <h1>{listing.title}</h1>
        <div><span className="detail-price">₹{Number(listing.price).toLocaleString('en-IN')}</span>{listing.listing_type === 'sell' && <span className="detail-price-note">Negotiable</span>}</div>
        <div className="detail-meta"><span className="soft-tag">{listing.category}</span><span className="soft-tag">{listing.condition.replace('-', ' ')}</span>{listing.subcategory && <span className="soft-tag">{listing.subcategory}</span>}<span className="soft-tag">{listing.listing_type}</span></div>
        <p style={{ fontSize: 13, lineHeight: 1.7, color: '#656b7d' }}>{listing.description}</p>
        <div className="seller-mini"><div className="seller-avatar">{listing.seller.display_name.charAt(0)}</div><div><strong>{listing.seller.display_name}</strong><span>★ {Number(listing.seller.reputation_score).toFixed(1)} · {listing.seller.completed_orders} completed transactions · {listing.seller.verified ? 'Verified seller' : 'Seller'}</span></div></div>
        <div className="detail-actions"><button className="btn btn-primary" disabled={unavailable} onClick={message}>{unavailable ? 'Listing unavailable' : 'Message seller'}</button><button className="btn btn-ghost" disabled={unavailable} onClick={() => setOfferOpen(true)}>Make offer</button><Link className="btn btn-ghost wide-action" href={`/swap?listing=${listing.id}`}>⇄ Swap this item</Link><button className={saved ? 'btn btn-soft' : 'btn btn-ghost'} onClick={save}>{saved ? '♥ Saved' : '♡ Save'}</button></div>
        <div className="pickup-card"><strong>Pickup details</strong><span>{listing.pickup_area || 'Campus pickup'}</span><span>{listing.campus_name ? `${listing.campus_name}, ${listing.campus_city || ''}${listing.campus_state ? `, ${listing.campus_state}` : ''}` : listing.campus_slug}</span><span>Landmark: {listing.pickup_landmark || 'Agreed with seller after acceptance'}</span><small>Exact private address details can be shared only inside the transaction when needed.</small></div>
        {error && <div className="error-box" style={{ marginTop: 12 }}>{error}</div>}
      </div>
    </div>
    <OfferModal open={offerOpen} onClose={() => setOfferOpen(false)} listing={listing} />
  </>;
}
