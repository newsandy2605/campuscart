'use client';
import { useState } from 'react';
import { addAddress, deleteAddress, type Address } from '../lib/api';

const empty = { label: 'Personal', line1: '', line2: '', locality: '', city: 'Pune', state: 'Maharashtra', pincode: '', landmark: '', is_default: false };

export default function AddressBook({ initial }: { initial: Address[] }) {
  const [items, setItems] = useState(initial);
  const [form, setForm] = useState({ ...empty });
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true); setError('');
    try {
      const item = await addAddress(form);
      setItems((prev) => form.is_default ? [item, ...prev.map((x) => ({ ...x, is_default: false }))] : [item, ...prev]);
      setForm({ ...empty });
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to save address');
    } finally { setBusy(false); }
  };

  const remove = async (id: number) => {
    try { await deleteAddress(id); setItems((prev) => prev.filter((x) => x.id !== id)); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to delete address'); }
  };

  return <div className="address-book">
    <div className="panel-head"><div><div className="eyebrow">PICKUP ADDRESSES</div><h2>Saved addresses</h2></div><button className="btn btn-primary" onClick={() => setOpen((x) => !x)}>＋ Add address</button></div>
    {open && <div className="address-form">
      <div className="form-grid">
        <label>Label<input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} /></label>
        <label>Pincode<input value={form.pincode} onChange={(e) => setForm({ ...form, pincode: e.target.value })} /></label>
        <label className="span-2">Address line<input value={form.line1} onChange={(e) => setForm({ ...form, line1: e.target.value })} placeholder="House / flat / building" /></label>
        <label>Locality<input value={form.locality} onChange={(e) => setForm({ ...form, locality: e.target.value })} /></label>
        <label>Landmark<input value={form.landmark} onChange={(e) => setForm({ ...form, landmark: e.target.value })} /></label>
      </div>
      <label className="address-default"><input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} /> Make this my default pickup address</label>
      {error && <div className="error-box">{error}</div>}
      <button className="btn btn-primary" disabled={busy || !form.line1 || !form.pincode} onClick={submit}>{busy ? 'Saving...' : 'Save address'}</button>
    </div>}
    {items.map((a) => <div className="address-row" key={a.id}><div><strong>{a.label}</strong>{a.is_default && <span className="verify">Default</span>}<p>{a.line1}{a.locality ? `, ${a.locality}` : ''}, {a.city}, {a.state} {a.pincode}</p>{a.landmark && <small>Landmark: {a.landmark}</small>}</div><button className="btn btn-ghost" onClick={() => remove(a.id)}>Delete</button></div>)}
    {!items.length && <div className="empty-state"><strong>No saved addresses</strong><span>Add one for private pickup details in transactions.</span></div>}
    {error && !open && <div className="error-box">{error}</div>}
  </div>;
}
