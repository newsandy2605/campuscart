 'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '../../components/AppShell';
import { getCampuses, getCampusMembership, getMe, joinCampus, setCampusSlug, type Campus, type AppUser } from '../../lib/api';

export default function CampusSelect() {
  const router = useRouter();
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [me, setMe] = useState<AppUser | null>(null);
  const [selected, setSelected] = useState('');
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [membership, setMembership] = useState<{ status: string; verified: boolean; verification_method?: string | null } | null>(null);

  useEffect(() => {
    Promise.all([getCampuses(), getMe()]).then(([cs, user]) => {
      setCampuses(cs); setMe(user);
      const domain = user.email?.split('@')[1]?.toLowerCase();
      const detected = cs.find((c) => (c.email_domains || [c.email_domain]).map((x) => x.toLowerCase()).includes(domain || ''));
      if (detected) setSelected(detected.slug);
    }).catch((e) => setError(e instanceof Error ? e.message : 'Unable to load campuses'));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return campuses;
    return campuses.filter((c) => `${c.name} ${c.city} ${c.state}`.toLowerCase().includes(q));
  }, [campuses, query]);

  const chosen = campuses.find((c) => c.slug === selected);
  const domainDetected = !!(chosen && me?.email && (chosen.email_domains || [chosen.email_domain]).map((x) => x.toLowerCase()).includes(me.email.split('@')[1]?.toLowerCase() || ''));

  const submit = async () => {
    if (!chosen) return;
    setBusy(true); setError('');
    try { const result = await joinCampus(chosen.slug); if (result.verified) { setCampusSlug(chosen.slug); router.push(`/campus/${chosen.slug}`); } else { setMembership(result); } }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to connect campus'); }
    finally { setBusy(false); }
  };

  useEffect(() => { if (selected) getCampusMembership(selected).then(setMembership).catch(()=>setMembership(null)); }, [selected]);

  return <AppShell active="Home"><div className="page-header"><div><div className="eyebrow">ONBOARDING</div><h1>Choose your campus</h1><p className="muted" style={{fontSize:13}}>Contact OTP verifies ownership of the contact. Institutional email or admin review verifies campus membership.</p></div></div><div className="panel campus-selector-panel"><div className="verified-badge">✓ Contact verified · {me?.phone || me?.email || 'loading...'}</div>{chosen&&<div className="detected-campus"><div><h2>{chosen.name}</h2><p>{chosen.city}, {chosen.state}</p><span>{domainDetected ? `✓ Institutional domain detected: ${chosen.email_domain}` : 'Campus selected manually by you'}</span></div>{domainDetected&&<span className="detected-pill">Detected</span>}</div>}<label>Search campuses<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by university, college or city"/></label><div className="campus-options">{filtered.map(c=><button type="button" key={c.id} className={selected===c.slug?'campus-option active':'campus-option'} onClick={()=>setSelected(c.slug)}><span><strong>{c.name}</strong><small>{c.city}, {c.state}</small></span><span>{selected===c.slug?'✓':'Select'}</span></button>)}</div>{filtered.length===0&&<div className="empty-state"><strong>No matching campus.</strong><span>Ask a CampusCart administrator to add the campus to the directory.</span></div>}{error&&<div className="error-box">{error}</div>}{membership?.verified ? <div className="success-box" style={{marginTop:12}}>✓ Membership verified via <strong>{membership.verification_method === 'institutional_email' ? 'institutional email' : membership.verification_method || 'verification'}</strong>.</div> : membership?.status === 'pending_review' ? <div className="success-box" style={{marginTop:12}}><strong>Verification pending.</strong><br/>An administrator must confirm that you belong to this campus. You cannot access marketplace features until the membership is approved.</div> : null}<button className="btn btn-primary" disabled={busy||!chosen||membership?.status==='pending_review'} onClick={submit}>{busy?'Submitting...':membership?.verified?'Open this campus':'Request campus access →'}</button><p className="muted small" style={{marginTop:10}}>Campus access requires institutional email-domain verification or administrator review. Development mode can optionally allow contact-OTP membership.</p></div></AppShell>;
}
