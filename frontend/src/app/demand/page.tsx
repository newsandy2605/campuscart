'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '../../components/AppShell';
import DemandRadar from '../../components/DemandRadar';
import { getDemandPulse, getDemandRadar, getPriceInsight, getCampusSlug, type DemandItem } from '../../lib/api';

export default function Demand() {
  const [items, setItems] = useState<DemandItem[]>([]);
  const [selected, setSelected] = useState('');
  const [tab, setTab] = useState('Top Demand');
  const [insight, setInsight] = useState<{ sample_size: number; low: number | null; median: number | null; high: number | null } | null>(null);
  const [pulse, setPulse] = useState({ active_listings: 0, wanted_posts: 0, completed_transactions: 0, total_traded: 0 });

  useEffect(() => { const s = getCampusSlug(); Promise.all([getDemandRadar(s), getDemandPulse(s)]).then(([r, p]) => { setItems(r.items); setPulse(p); setSelected(r.items[0]?.name || ''); }).catch(() => {}); }, []);
  useEffect(() => { if (tab === 'Price Insights' && selected) getPriceInsight(getCampusSlug(), selected).then(setInsight).catch(() => setInsight(null)); }, [tab, selected]);
  const top = items.find((x) => x.name === selected) || items[0];

  return <AppShell active="Demand Radar"><div className="page-header"><div><div className="eyebrow">MARKET INTELLIGENCE</div><h1>Campus Demand Radar</h1><p className="muted" style={{ fontSize: 13, marginTop: 4 }}>Understand demand before you decide what to list.</p></div><Link href="/seller/new" className="btn btn-primary">List an item</Link></div>
    <div className="stat-grid"><div className="stat-card"><strong>{pulse.wanted_posts}</strong><span>open wanted posts</span></div><div className="stat-card violet"><strong>{pulse.active_listings}</strong><span>active listings</span></div><div className="stat-card green"><strong>₹{Number(pulse.total_traded).toLocaleString('en-IN')}</strong><span>campus value traded</span></div><div className="stat-card"><strong>{pulse.completed_transactions}</strong><span>completed transactions</span></div></div>
    <div className="panel"><div className="category-row">{['Top Demand','Trending','Seasonal','Price Insights'].map((x) => <button key={x} onClick={() => setTab(x)} className={tab === x ? 'category-chip active' : 'category-chip'}>{x}</button>)}</div>{tab === 'Price Insights' && selected ? <div className="price-insight-card"><div><div className="eyebrow">SELECTED CATEGORY</div><h2>{selected}</h2></div><div className="price-insight-grid"><div><span>Low</span><strong>₹{insight?.low ?? '—'}</strong></div><div><span>Median</span><strong>₹{insight?.median ?? '—'}</strong></div><div><span>High</span><strong>₹{insight?.high ?? '—'}</strong></div><div><span>Sample size</span><strong>{insight?.sample_size ?? 0}</strong></div></div></div> : <DemandRadar />}</div>
    <div className="dashboard-grid"><div className="panel"><div className="panel-head"><h2>{top?.name || 'Top demand category'}</h2><span className="verified-badge">{top?.trend ? `Recent interest ${top.trend}` : 'Demand signal'}</span></div><div className="demand-category-picker">{items.map((x) => <button key={x.name} className={selected === x.name ? 'demand-choice active' : 'demand-choice'} onClick={() => setSelected(x.name)}><strong>{x.name}</strong><span>{x.wanted} wanted · {x.supply} active</span></button>)}</div><div className="stat-grid"><div className="stat-card violet"><strong>{top?.wanted || 0}</strong><span>students want this</span></div><div className="stat-card"><strong>{top?.supply || 0}</strong><span>active listings</span></div><div className="stat-card green"><strong>{top?.range || '—'}</strong><span>typical price range</span></div><div className="stat-card"><strong>{top ? `${(top.wanted / Math.max(1, top.supply)).toFixed(1)}×` : '—'}</strong><span>demand / supply</span></div></div></div><div className="panel"><div className="eyebrow">SELLER SIGNAL</div><h2 style={{ fontSize: 18 }}>Demand can guide your next listing</h2><p className="muted" style={{ fontSize: 11 }}>CampusCart aggregates wanted posts, active inventory and accepted-sale pricing.</p><Link href="/seller/new" className="btn btn-primary">Create listing</Link></div></div>
  </AppShell>;
}
