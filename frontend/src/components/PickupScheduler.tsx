'use client';

import { useEffect, useState } from 'react';
import { getAddresses, schedulePickup, type Address, type Campus, type Transaction } from '../lib/api';

export default function PickupScheduler({
  transaction,
  campus,
  onUpdate,
}: {
  transaction: Transaction;
  campus: Campus | null;
  onUpdate: (tx: Transaction) => void;
}) {
  const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  const [mode, setMode] = useState<'campus' | 'address'>('campus');
  const [location, setLocation] = useState(String(transaction.pickup_location_id || campus?.pickup_locations?.[0]?.id || ''));
  const [addressId, setAddressId] = useState('');
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [date, setDate] = useState(transaction.pickup_date || tomorrow);
  const [time, setTime] = useState(transaction.pickup_time?.slice(0, 5) || '17:30');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (transaction.status === 'paid' || transaction.status === 'swap_accepted') {
      getAddresses().then(setAddresses).catch(() => {});
    }
  }, [transaction.status]);

  useEffect(() => {
    if (!location && campus?.pickup_locations?.[0]) {
      setLocation(String(campus.pickup_locations[0].id));
    }
  }, [campus, location]);

  if (!['paid', 'swap_accepted'].includes(transaction.status)) return null;

  const submit = async () => {
    if ((mode === 'campus' && !location) || (mode === 'address' && !addressId)) return;
    setBusy(true);
    setError('');
    try {
      const result = await schedulePickup(transaction.id, {
        pickup_location_id: mode === 'campus' ? Number(location) : undefined,
        pickup_address_id: mode === 'address' ? Number(addressId) : undefined,
        pickup_date: date,
        pickup_time: `${time}:00`,
      });
      onUpdate(result.transaction);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to schedule pickup');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="pickup-scheduler">
      <div className="eyebrow">{transaction.status === 'swap_accepted' ? 'SCHEDULE SWAP PICKUP' : 'SCHEDULE PICKUP'}</div>
      <h3>Choose when and where to meet</h3>

      <div className="auth-tabs pickup-tabs">
        <button type="button" className={mode === 'campus' ? 'auth-tab active' : 'auth-tab'} onClick={() => setMode('campus')}>Campus point</button>
        <button type="button" className={mode === 'address' ? 'auth-tab active' : 'auth-tab'} onClick={() => setMode('address')}>Saved address</button>
      </div>

      {mode === 'campus' ? (
        <label>
          Pickup point
          <select value={location} onChange={(event) => setLocation(event.target.value)}>
            {campus?.pickup_locations?.map((point) => (
              <option key={point.id} value={point.id}>{point.name} · {point.address}</option>
            ))}
          </select>
        </label>
      ) : (
        <label>
          Private pickup address
          <select value={addressId} onChange={(event) => setAddressId(event.target.value)}>
            <option value="">Select saved address</option>
            {addresses.map((address) => (
              <option key={address.id} value={address.id}>{address.label} · {address.locality}, {address.city}</option>
            ))}
          </select>
        </label>
      )}

      <div className="form-grid" style={{ marginTop: 10 }}>
        <label>Date<input type="date" min={tomorrow} value={date} onChange={(event) => setDate(event.target.value)} /></label>
        <label>Time<input type="time" value={time} onChange={(event) => setTime(event.target.value)} /></label>
      </div>

      {error && <div className="error-box">{error}</div>}
      <button className="btn btn-primary full" disabled={busy || (mode === 'campus' ? !location : !addressId)} onClick={submit}>
        {busy ? 'Scheduling...' : 'Schedule pickup'}
      </button>
    </div>
  );
}
