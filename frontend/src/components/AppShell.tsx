'use client';
import type { PropsWithChildren } from 'react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from './Sidebar';

type Props = PropsWithChildren<{ active?: string }>;
export default function AppShell({ children, active }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem('campuscart_token')) router.replace('/login');
    else setReady(true);
  }, [router]);
  if (!ready) return <div className="app-loading"><div className="loading-dot" /> Loading CampusCart...</div>;
  return <div className="app-shell"><Sidebar active={active} /><main className="app-main">{children}</main></div>;
}
