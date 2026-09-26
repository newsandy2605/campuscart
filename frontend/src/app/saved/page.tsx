
'use client';
import Link from 'next/link';
import { useEffect,useState } from 'react';
import AppShell from '../../components/AppShell';
import ProductCard from '../../components/ProductCard';
import { getFavorites,type Listing } from '../../lib/api';
export default function SavedItems(){const [items,setItems]=useState<Listing[]>([]);const [error,setError]=useState('');useEffect(()=>{getFavorites().then(setItems).catch(e=>setError(e instanceof Error?e.message:'Unable to load saved items'))},[]);return <AppShell active="Saved Items"><div className="page-header"><div><div className="eyebrow">YOUR CAMPUSCART</div><h1>Saved items</h1><p className="muted" style={{fontSize:13}}>Listings you bookmarked for later.</p></div><Link href="/marketplace" className="btn btn-primary">Browse marketplace</Link></div>{error?<div className="error-box">{error}</div>:items.length?<div className="product-grid-v2">{items.map(item=><ProductCard key={item.id} listing={item}/>)}</div>:<div className="panel empty-state"><strong>No saved items yet.</strong><span>Tap the heart on a marketplace listing to keep it here.</span><Link href="/marketplace" className="btn btn-soft" style={{margin:'8px auto 0'}}>Explore Marketplace →</Link></div>}</AppShell>}
