'use client';
import { useEffect, useState } from 'react';
import { getDemandRadar, getCampusSlug, type DemandItem } from '../lib/api';
export default function DemandRadar({ compact = false }: { compact?: boolean }) {
  const [items,setItems]=useState<DemandItem[]>([]); const [loading,setLoading]=useState(true);
  useEffect(()=>{getDemandRadar(getCampusSlug()).then(r=>setItems(r.items)).catch(()=>{}).finally(()=>setLoading(false));},[]);
  if(loading) return <div className="muted small">Loading demand signals...</div>;
  return <div className={compact ? 'demand-list compact' : 'demand-list'}>{items.map(item=><div key={item.name} className="demand-row"><div><strong>{item.name}</strong><span>{item.wanted} wants · {item.supply} listed</span></div><div className="demand-bar"><i style={{width:`${Math.min(96, Math.max(8, item.wanted*2))}%`}} /></div>{!compact&&<div className="demand-right"><strong>{item.trend}</strong><span>{item.range}</span></div>}</div>)}</div>;
}
