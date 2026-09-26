 'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import Logo from '../../components/Logo';
import { registerUser, setSession } from '../../lib/api';

export default function Register() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [channel, setChannel] = useState<'email' | 'phone'>('email');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const create = async () => {
    setError('');
    setBusy(true);
    try {
      const data = await registerUser({
        name,
        email: email || undefined,
        phone: phone || undefined,
        password,
        verification_channel: channel,
      });
      setSession(data);
      if (data.otp_delivery?.debug_code) {
        localStorage.setItem('campuscart_otp_debug', data.otp_delivery.debug_code);
      } else {
        localStorage.removeItem('campuscart_otp_debug');
      }
      const destination = channel === 'email' ? email : phone;
      router.push(`/verify?channel=${channel}&destination=${encodeURIComponent(destination)}&purpose=${channel === 'email' ? 'email_verification' : 'phone_verification'}&next=/campus`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to register');
    } finally {
      setBusy(false);
    }
  };

  const contactReady = channel === 'email' ? !!email : !!phone;

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <Logo />
          <div>
            <div className="eyebrow" style={{ color: '#bcaeff' }}>JOIN CAMPUSCART</div>
            <h2>Create your student account.</h2>
            <p>Verify an email address or phone number with OTP, then choose the campus you want to use.</p>
          </div>
          <div className="auth-proof">
            <span>1 · Verify email or phone with OTP</span>
            <span>2 · Choose your campus</span>
            <span>3 · Buy, sell and swap locally</span>
          </div>
        </div>

        <div className="auth-form">
          <div className="eyebrow">CREATE ACCOUNT</div>
          <h2>Tell us about you</h2>

          <label>Full name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" /></label>

          <div className="auth-tabs">
            <button type="button" className={channel === 'email' ? 'auth-tab active' : 'auth-tab'} onClick={() => setChannel('email')}>Email OTP</button>
            <button type="button" className={channel === 'phone' ? 'auth-tab active' : 'auth-tab'} onClick={() => setChannel('phone')}>Phone OTP</button>
          </div>

          {channel === 'email' ? (
            <label>Email address<input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@gmail.com or you@university.ac.in" type="email" /></label>
          ) : (
            <label>Phone number<input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 XXXXX XXXXX" inputMode="tel" /></label>
          )}

          {channel === 'email' && <label>Phone number <span className="muted">(optional)</span><input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 XXXXX XXXXX" inputMode="tel" /></label>}
          {channel === 'phone' && <label>Email address <span className="muted">(optional)</span><input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@gmail.com or university email" type="email" /></label>}

          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" /></label>

          {error && <div className="error-box">{error}</div>}
          <button className="btn btn-primary full" disabled={busy || !name || !contactReady || password.length < 8} onClick={create}>{busy ? 'Creating...' : `Create account & send ${channel} OTP`}</button>
          <div className="auth-foot">Campus affiliation is selected after OTP verification. No university email domain is required.</div>
          <div className="auth-foot">Already have an account? <Link href="/login">Log in</Link></div>
        </div>
      </div>
    </main>
  );
}
