'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import AppShell from '../../../components/AppShell';
import { getCampusSlug, getCampus, type Campus } from '../../../lib/api';

export default function OnboardingSuccess(){
  const [campus,setCampus]=useState<Campus|null>(null);
  const slug=getCampusSlug();
  useEffect(()=>{ if(slug) void getCampus(slug).then(setCampus).catch(()=>{}); },[slug]);
  const href=slug?`/campus/${slug}`:'/campus';
  return <AppShell active="Home"><div className="panel" style={{maxWidth:680,margin:'12vh auto',textAlign:'center',padding:'58px 44px'}}><div className="success-coin" style={{margin:'0 auto'}}>✓</div><div className="eyebrow" style={{marginTop:18}}>ONBOARDING COMPLETE</div><h1 style={{fontSize:42}}>You're all set.</h1><p className="muted">Welcome to CampusCart. {campus?.name || 'Your selected campus'} is now ready for your marketplace.</p><div className="auth-proof" style={{margin:'24px auto',maxWidth:360}}><span>✓ Contact verified</span><span>✓ Campus selected</span><span>✓ Marketplace ready</span></div><Link className="btn btn-primary" href={href}>Continue to Campus →</Link></div></AppShell>;
}
