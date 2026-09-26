'use client';
import { useEffect, useState } from 'react';
import AppShell from '../../components/AppShell';
import AddressBook from '../../components/AddressBook';
import { clearSession, getAddresses, getMe, getSellerAnalytics, type Address, type AppUser } from '../../lib/api';
import { useRouter } from 'next/navigation';

export default function Profile() {
  const router = useRouter();
  const [me, setMe] = useState<AppUser | null>(null);
  const [analytics, setAnalytics] = useState<{ active_listings: number; completed_orders: number; reputation_score: number } | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  useEffect(() => { Promise.all([getMe(), getAddresses()]).then(([u, a]) => { setMe(u); setAddresses(a); }).catch(() => {}); getSellerAnalytics().then(setAnalytics).catch(() => {}); }, []);
  return <AppShell active="Profile"><div className="page-header"><div><div className="eyebrow">ACCOUNT</div><h1>Profile</h1></div><button className="btn btn-ghost" onClick={() => { clearSession(); router.replace('/login'); }}>Sign out</button></div><div className="profile-grid"><section><div className="profile-hero"><div className="profile-big">{(me?.name || 'S').charAt(0)}</div><div><h2>{me?.name || 'Student'}</h2><p>{me?.email || ''}</p><div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}><span className="verified-badge">{me?.email_verified ? '✓ Email verified' : 'Email pending'}</span><span className="verified-badge">{me?.phone_verified ? '✓ Phone verified' : 'Phone pending'}</span><span className="verified-badge">{me?.campuses?.find((x) => x.verified) ? '✓ Campus verified' : 'Campus pending'}</span></div></div></div><div className="profile-stat-row"><div className="profile-stat"><strong>{analytics?.active_listings || 0}</strong><span>Active listings</span></div><div className="profile-stat"><strong>{analytics?.completed_orders || 0}</strong><span>Completed transactions</span></div><div className="profile-stat"><strong>{analytics?.reputation_score ? Number(analytics.reputation_score).toFixed(1) : '—'}</strong><span>Reputation</span></div></div></section><section className="panel"><div className="eyebrow">PERSONAL INFORMATION</div><div className="setting-list"><div className="setting-row"><div><strong>Email</strong><span>{me?.email}</span></div></div><div className="setting-row"><div><strong>Phone</strong><span>{me?.phone || 'Not added'}</span></div></div><div className="setting-row"><div><strong>Campus</strong><span>{me?.campuses?.find((x) => x.verified)?.name || 'Not verified'}</span></div></div></div></section></div><div className="panel" style={{ marginTop: 18 }}><AddressBook initial={addresses}/></div></AppShell>;
}
