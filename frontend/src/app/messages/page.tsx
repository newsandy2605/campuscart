'use client';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import AppShell from '../../components/AppShell';
import ChatPanel from '../../components/ChatPanel';
import { createConversation, listConversations, type Conversation } from '../../lib/api';

export default function Messages() {
  const params = useSearchParams();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const selectedParam = Number(params.get('conversation') || 0);
  const listingParam = Number(params.get('listing') || 0);

  const load = async () => {
    try { setConversations(await listConversations()); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to load messages'); }
  };

  useEffect(() => {
    load();
    if (!selectedParam && listingParam) {
      createConversation(listingParam).then((c) => router.replace(`/messages?conversation=${c.id}`)).catch((e) => setError(e instanceof Error ? e.message : 'Unable to start conversation'));
    }
  }, [selectedParam, listingParam, router]);

  const filtered = useMemo(() => conversations.filter((c) => (c.listing_title || '').toLowerCase().includes(query.toLowerCase()) || (c.seller_name || '').toLowerCase().includes(query.toLowerCase()) || (c.buyer_name || '').toLowerCase().includes(query.toLowerCase())), [query, conversations]);
  const selected = selectedParam || filtered[0]?.id;

  return <AppShell active="Messages"><div className="page-header"><div><div className="eyebrow">CONVERSATIONS</div><h1>Messages</h1></div></div>{error && <div className="error-box">{error}</div>}<div className="chat-layout"><div className="conversation-list"><div className="conversation-search"><input className="search-input" style={{ width: '100%' }} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search conversations..." /></div>{filtered.map((c) => <button key={c.id} className={selected === c.id ? 'conversation-item active' : 'conversation-item'} onClick={() => router.push(`/messages?conversation=${c.id}`)}><div className="mini-avatar">{(c.seller_name || c.buyer_name || '?').charAt(0)}</div><div style={{ minWidth: 0, flex: 1 }}><strong>{c.seller_name || c.buyer_name || 'Student'}</strong><span>{c.listing_title || `Listing #${c.listing_id}`}</span><div className="conversation-preview">{c.last_message_at ? new Date(c.last_message_at).toLocaleString('en-IN') : 'No messages yet'}</div></div></button>)}{!filtered.length && <div className="empty-state"><strong>No conversations yet</strong><span>Open a listing and message the seller to start.</span></div>}</div><ChatPanel conversationId={selected} /></div></AppShell>;
}
