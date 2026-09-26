 'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { createPaymentOrder, verifyPayment, type Transaction } from '../lib/api';

type RazorpayInstance = { open: () => void };
type RazorpayConstructor = new (options: Record<string, unknown>) => RazorpayInstance;

declare global { interface Window { Razorpay?: RazorpayConstructor } }

export default function PaymentAnimation({ transaction }: { transaction: Transaction }) {
  const [state, setState] = useState<'processing'|'success'|'failed'>('processing');
  const [error, setError] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    let cancelled = false;

    (async () => {
      try {
        const order = await createPaymentOrder(transaction.id);
        if (cancelled) return;

        if (order.provider === 'razorpay' && order.key_id) {
          const openCheckout = () => {
            if (!window.Razorpay) throw new Error('Razorpay Checkout failed to load');
            const checkout = new window.Razorpay({
              key: order.key_id,
              amount: Number((order.order as { amount?: number }).amount || 0),
              currency: 'INR',
              name: 'CampusCart',
              description: transaction.listing_title || 'CampusCart purchase',
              order_id: String((order.order as { id?: string }).id || ''),
              handler: async (response: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) => {
                try {
                  await verifyPayment({ provider_order_id: response.razorpay_order_id, provider_payment_id: response.razorpay_payment_id, signature: response.razorpay_signature });
                  setState('success');
                } catch (e) {
                  setError(e instanceof Error ? e.message : 'Payment verification failed');
                  setState('failed');
                }
              },
              modal: { ondismiss: () => setState('failed') },
              prefill: { name: transaction.buyer_name || '' },
              theme: { color: '#5d35f5' },
            });
            checkout.open();
          };

          if (!window.Razorpay) {
            const script = document.createElement('script');
            script.src = 'https://checkout.razorpay.com/v1/checkout.js';
            script.async = true;
            script.onload = openCheckout;
            script.onerror = () => { setError('Unable to load Razorpay Checkout'); setState('failed'); };
            document.body.appendChild(script);
          } else {
            openCheckout();
          }
        } else {
          setTimeout(async () => {
            try {
              await verifyPayment({ provider_order_id: String((order.order as { id?: string }).id || ''), provider_payment_id: `local_pay_${transaction.id}`, signature: 'local' });
              setState('success');
            } catch (e) {
              setError(e instanceof Error ? e.message : 'Payment verification failed');
              setState('failed');
            }
          }, 900);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unable to start payment');
        setState('failed');
      }
    })();

    return () => { cancelled = true; };
  }, [transaction.id, transaction.buyer_name, transaction.listing_title]);

  return <div className={`payment-stage ${state}`}>{state==='processing'&&<><div className="coin-spinner">₹</div><h2>Processing your payment...</h2><p>Opening secure UPI checkout</p><div className="payment-steps"><span className="done">Create order</span><span className="current">Authorise</span><span>Confirm</span></div></>}{state==='success'&&<><div className="success-coin">₹</div><div className="check-orb">✓</div><h2>Payment successful</h2><strong className="payment-amount">₹{Number(transaction.agreed_price).toLocaleString('en-IN')}</strong><p>Payment confirmed · Transaction #{transaction.id}</p><Link href={`/transactions/${transaction.id}`} className="btn btn-primary">View Transaction</Link></>}{state==='failed'&&<><div className="failure-orb">!</div><h2>Payment not completed</h2><p>{error||'No successful payment was recorded.'}</p><button className="btn btn-primary" onClick={()=>window.location.reload()}>Try again</button></>}</div>;
}
