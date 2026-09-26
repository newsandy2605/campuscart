 'use client';
import Link from 'next/link';
import { useState } from 'react';
import Logo from '../../components/Logo';
import { loginUser, requestOtp, setSession } from '../../lib/api';
import { useRouter } from 'next/navigation';

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<'password' | 'otp'>('password');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [destination, setDestination] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submitPassword = async () => {
    setError(''); setBusy(true);
    try { const data = await loginUser({ identifier, password }); setSession(data); router.push('/campus'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to sign in'); }
    finally { setBusy(false); }
  };

  const sendCode = async () => {
    setError(''); setBusy(true);
    try {
      const channel = destination.includes('@') ? 'email' : 'phone';
      const data = await requestOtp({ channel, destination, purpose: 'login' });
      if (data.otp_delivery?.debug_code) localStorage.setItem('campuscart_otp_debug', data.otp_delivery.debug_code);
      router.push(`/verify?channel=${channel}&destination=${encodeURIComponent(destination)}&purpose=login&next=/campus`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to send OTP'); }
    finally { setBusy(false); }
  };

  return <main className="auth-page"><div className="auth-card"><div className="auth-brand"><Logo/><div><div className="eyebrow" style={{color:'#bcaeff'}}>CAMPUSCART ACCESS</div><h2>Buy from your campus. Sell to your campus.</h2><p>Use your email address or phone number. Campus selection happens after verification.</p></div><div className="auth-proof"><span>✓ Email or phone OTP</span><span>✓ Campus marketplace</span><span>✓ Local pickup & UPI</span></div></div><div className="auth-form"><div className="eyebrow">WELCOME BACK</div><h2>Sign in to CampusCart</h2><div className="auth-tabs"><button className={mode==='password'?'auth-tab active':'auth-tab'} onClick={()=>setMode('password')}>Password</button><button className={mode==='otp'?'auth-tab active':'auth-tab'} onClick={()=>setMode('otp')}>OTP</button></div>{mode==='password'?<><label>Email or phone<input value={identifier} onChange={e=>setIdentifier(e.target.value)} placeholder="you@gmail.com or +91..."/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password"/></label><button className="btn btn-primary full" disabled={busy||!identifier||!password} onClick={submitPassword}>{busy?'Signing in...':'Continue'}</button></>:<><label>Email or phone<input value={destination} onChange={e=>setDestination(e.target.value)} placeholder="you@gmail.com or +91..."/></label><button className="btn btn-primary full" disabled={busy||!destination} onClick={sendCode}>{busy?'Sending...':'Send OTP'}</button></>}{error&&<div className="error-box">{error}</div>}<div className="auth-foot"><Link href="/forgot-password">Forgot password?</Link></div><div className="auth-foot">Don't have an account? <Link href="/register">Sign up</Link></div></div></div></main>;
}
