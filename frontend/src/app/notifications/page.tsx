'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '../../components/AppShell';
import { getNotifications, markNotificationRead, type Notification } from '../../lib/api';

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [tab, setTab] = useState('All');
  useEffect(() => { getNotifications().then(setItems).catch(() => {}); }, []);
  const filtered = tab === 'All' ? items : items.filter((n) => n.kind.toLowerCase() === tab.toLowerCase().replace(' ', '_'));
  const read = async (n: Notification) => { if (!n.read) { await markNotificationRead(n.id).catch(() => {}); setItems((prev) => prev.map((x) => x.id === n.id ? { ...x, read: true } : x)); } };
  return <AppShell active="Notifications"><div className="page-header"><div><div className="eyebrow">ACTIVITY</div><h1>Notifications</h1></div></div><div className="category-row notification-tabs">{['All','Messages','Offers','Transactions'].map((x) => <button key={x} className={tab === x ? 'category-chip active' : 'category-chip'} onClick={() => setTab(x)}>{x}</button>)}</div><div className="panel notification-list">{filtered.map((n) => <Link href={n.link || '#'} onClick={() => read(n)} key={n.id} className={n.read ? 'notification-row' : 'notification-row unread'}><span className="notification-icon">{n.kind === 'payment' ? '₹' : n.kind === 'message' ? '✉' : n.kind === 'offer' ? '↔' : n.kind === 'pickup' ? '⌖' : '●'}</span><div><strong>{n.title}</strong><p>{n.body}</p><small>{new Date(n.created_at).toLocaleString('en-IN')}</small></div></Link>)}{!filtered.length && <div className="empty-state"><strong>No notifications here</strong><span>New offers, messages and transaction updates will appear here.</span></div>}</div></AppShell>;
}
