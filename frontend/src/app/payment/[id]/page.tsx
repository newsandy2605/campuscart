'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import AppShell from '../../../components/AppShell';
import PaymentAnimation from '../../../components/PaymentAnimation';
import { getTransaction, type Transaction } from '../../../lib/api';

export default function Payment() {
  const { id } = useParams<{ id: string }>();
  const [tx, setTx] = useState<Transaction | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { if (!id) return; getTransaction(Number(id)).then(setTx).catch((e) => setError(e instanceof Error ? e.message : 'Unable to load payment')); }, [id]);
  return <AppShell active="Transactions"><div className="payment-page">{error ? <div className="error-box">{error}</div> : tx ? <PaymentAnimation transaction={tx} /> : <div className="muted">Loading payment...</div>}</div></AppShell>;
}
