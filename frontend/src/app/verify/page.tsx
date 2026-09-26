 'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { ClipboardEvent, KeyboardEvent } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Logo from '../../components/Logo';
import { requestOtp, setSession, verifyOtp } from '../../lib/api';

function VerifyContent() {
  const params = useSearchParams();
  const router = useRouter();
  const channel = params.get('channel') === 'phone' ? 'phone' : 'email';
  const purpose = params.get('purpose') || (channel === 'email' ? 'email_verification' : 'phone_verification');
  const destination = params.get('destination') || '';
  const next = params.get('next') || '/campus';

  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [verified, setVerified] = useState(false);
  const [devCode, setDevCode] = useState('');
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);

  const code = digits.join('');
  const display = useMemo(() => channel === 'email' ? destination : destination.replace(/(\+91|\d{2})(\d+)(\d{4})/, '$1 ••••••$3'), [channel, destination]);

  useEffect(() => {
    const saved = localStorage.getItem('campuscart_otp_debug');
    if (saved) setDevCode(saved);
  }, []);

  const setCode = (value: string, index: number) => {
    const clean = value.replace(/\D/g, '').slice(-1);
    const nextDigits = [...digits];
    nextDigits[index] = clean;
    setDigits(nextDigits);
    if (clean && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>, index: number) => {
    if (event.key === 'Backspace' && !digits[index] && index > 0) inputRefs.current[index - 1]?.focus();
  };

  const handlePaste = (event: ClipboardEvent<HTMLInputElement>) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    event.preventDefault();
    setDigits(pasted.split('').concat(Array(6).fill('')).slice(0, 6));
    inputRefs.current[Math.min(pasted.length, 6) - 1]?.focus();
  };

  const submit = async () => {
    setError('');
    setBusy(true);
    try {
      const data = await verifyOtp({ channel, destination, code, purpose });
      localStorage.removeItem('campuscart_otp_debug');
      if (data.token) setSession(data);
      setVerified(true);
      setTimeout(() => router.push(next), 450);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid OTP');
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    setError('');
    setDigits(['', '', '', '', '', '']);
    try {
      const data = await requestOtp({ channel, destination, purpose });
      if (data.otp_delivery?.debug_code) {
        localStorage.setItem('campuscart_otp_debug', data.otp_delivery.debug_code);
        setDevCode(data.otp_delivery.debug_code);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to resend');
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <Logo />
          <div>
            <div className="eyebrow" style={{ color: '#bcaeff' }}>SECURE VERIFICATION</div>
            <h2>Verify your contact with a one-time code.</h2>
            <p>Your campus is selected separately. An OTP proves you control the email address or phone number you entered.</p>
          </div>
          <div className="auth-proof">
            <span>✓ Six-digit OTP</span>
            <span>✓ Email or phone</span>
            <span>✓ Campus selection comes next</span>
          </div>
        </div>

        <div className="auth-form">
          {verified ? (
            <>
              <div className="verified-badge">✓ {channel === 'email' ? 'Email' : 'Phone'} verified</div>
              <h2>Verified.</h2>
              <p className="muted" style={{ fontSize: 12 }}>Taking you to campus selection…</p>
              <Link href={next} className="btn btn-primary full">Continue →</Link>
            </>
          ) : (
            <>
              <div className="eyebrow">OTP VERIFICATION</div>
              <h2>Verify your {channel}</h2>
              <p className="muted" style={{ fontSize: 12 }}>Code sent to <strong>{display || 'your contact'}</strong></p>

              <div className="otp-boxes" onPaste={handlePaste}>
                {digits.map((value, index) => (
                  <input key={index} ref={(node) => { inputRefs.current[index] = node; }} inputMode="numeric" maxLength={1} value={value} onChange={(e) => setCode(e.target.value, index)} onKeyDown={(e) => handleKeyDown(e, index)} aria-label={`OTP digit ${index + 1}`} />
                ))}
              </div>

              {devCode && <div className="success-box" style={{ marginBottom: 10 }}>Development OTP: <strong>{devCode}</strong></div>}
              {error && <div className="error-box">{error}</div>}

              <button className="btn btn-primary full" disabled={busy || code.length !== 6} onClick={submit}>{busy ? 'Verifying...' : 'Verify code'}</button>
              <button className="btn btn-ghost full" style={{ marginTop: 8 }} onClick={resend}>Send a new code</button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return <Suspense fallback={<main className="auth-page"><div className="auth-card"><div className="auth-form">Loading verification...</div></div></main>}><VerifyContent /></Suspense>;
}
