'use client';
import { useEffect, useState } from 'react';
import { blockConversation, getConversation, getMe, sendMessage, type AppUser, type Conversation, type Message } from '../lib/api';

export default function ChatPanel({ conversationId, fallbackSeller = 'CampusCart seller', fallbackListing = 'Listing' }: { conversationId?: number; fallbackSeller?: string; fallbackListing?: string }) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [me, setMe] = useState<AppUser | null>(null);
  const [value, setValue] = useState('');
  const [error, setError] = useState('');
  const [blocked, setBlocked] = useState(false);

  const load = async () => {
    if (!conversationId) return;
    try {
      const [data, user] = await Promise.all([getConversation(conversationId), getMe()]);
      setConversation(data.conversation);
      setMessages(data.messages);
      setMe(user);
      setBlocked(data.conversation.blocked);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load conversation');
    }
  };

  useEffect(() => { load(); }, [conversationId]);

  const submit = async () => {
    if (!conversationId || !value.trim() || blocked) return;
    try {
      const m = await sendMessage(conversationId, value.trim());
      setMessages((prev) => [...prev, m]);
      setValue('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to send message');
    }
  };

  const block = async () => {
    if (!conversationId) return;
    try {
      await blockConversation(conversationId);
      setBlocked(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to block conversation');
    }
  };

  if (!conversationId) {
    return <div className="chat-window chat-empty"><div className="empty-state"><strong>Select a conversation</strong><span>Open a campus listing and message the seller to start.</span></div></div>;
  }

  const otherName = me?.id === conversation?.seller_id ? conversation?.buyer_name : conversation?.seller_name;

  return <div className="chat-window">
    <div className="chat-head">
      <div><strong>{otherName || fallbackSeller}</strong><span>● Campus verified</span></div>
      <div className="chat-head-right"><span className="muted">{conversation?.listing_title || fallbackListing}</span><button className="chat-block" onClick={block} disabled={blocked}>{blocked ? 'Blocked' : 'Block'}</button></div>
    </div>
    <div className="chat-body">
      {messages.map((m) => <div key={m.id} className={m.sender_id === me?.id ? 'bubble-row me' : 'bubble-row'}>
        <div className={m.sender_id === me?.id ? 'bubble bubble-me' : 'bubble'}>
          {m.body}<span>{new Date(m.created_at).toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' })}</span>
        </div>
      </div>)}
      {!messages.length && <div className="empty-state"><strong>No messages yet</strong><span>Start the conversation about this listing.</span></div>}
    </div>
    <div className="chat-compose">
      <input disabled={blocked} value={value} onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submit(); }} placeholder={blocked ? 'This conversation is blocked' : 'Type a message...'} />
      <button disabled={blocked || !value.trim()} onClick={submit}>Send</button>
    </div>
    {error && <div className="error-box">{error}</div>}
  </div>;
}
