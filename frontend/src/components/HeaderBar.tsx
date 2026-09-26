import type { ReactNode } from 'react';
import Link from 'next/link';

export default function HeaderBar({ title, eyebrow, action }: { title: string; eyebrow?: string; action?: ReactNode }) {
  return <div className="page-header"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1></div><div className="page-actions">{action || <><Link href="/notifications" className="icon-button">◌</Link><div className="avatar">S</div></>}</div></div>;
}
