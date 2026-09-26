'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { favoriteListing, getFavoriteIds, removeFavorite, saveFavorite, type Listing } from '../lib/api';

export default function ProductCard({ listing }: { listing: Listing }) {
  const [saved, setSaved] = useState(false);
  useEffect(() => { getFavoriteIds().then(r => setSaved(r.listing_ids.includes(listing.id))).catch(() => {}); }, [listing.id]);
  useEffect(() => { getFavoriteIds().then(r => setSaved(r.listing_ids.includes(listing.id))).catch(() => {}); }, [listing.id]);
  const image = listing.images?.[0]?.url || '/products/math.svg';
  const distance = listing.distance_km != null ? `${Number(listing.distance_km).toFixed(1)} km` : 'campus';
  const created = listing.created_at ? new Date(listing.created_at).toLocaleString('en-IN', { hour: 'numeric', minute: '2-digit' }) : '';
  return <article className="product-card-v2">
    <div className="product-photo">
      <Link href={`/marketplace/${listing.id}`} aria-label={`View ${listing.title}`}><img src={image} alt={listing.images?.[0]?.alt || listing.title} /></Link>
      <button type="button" className={saved ? 'save-btn saved' : 'save-btn'} aria-label={saved ? 'Remove from saved items' : 'Save listing'} onClick={async () => { try { const result = saved ? await removeFavorite(listing.id) : await saveFavorite(listing.id); setSaved(result.saved); } catch {} }}>♡</button>
      <span className="photo-time">{created}</span>
    </div>
    <div className="product-copy">
      <div className="product-title-row"><div><h3><Link href={`/marketplace/${listing.id}`}>{listing.title}</Link></h3><div className="muted small">{listing.condition.replace('-', ' ')} · {listing.category}</div></div><strong>₹{Number(listing.price).toLocaleString('en-IN')}</strong></div>
      <div className="tag-line"><span className="verify">✓ Verified</span>{listing.listing_type === 'sell' && <span className="soft-tag">Negotiable</span>}<span className="muted small">◉ {distance}</span></div>
      <div className="card-bottom"><span className="muted small">{listing.pickup_area || listing.pickup_landmark || 'Campus pickup'}</span><Link href={`/marketplace/${listing.id}`} className="card-link">View →</Link></div>
    </div>
  </article>;
}
