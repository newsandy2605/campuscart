import Link from 'next/link';
import Logo from './Logo';

export default function PublicHeader() {
  return <header className="public-header">
    <Logo />
    <nav>
      <Link href="/marketplace">Discover</Link>
      <Link href="/marketplace">Marketplace</Link>
      <Link href="/wanted">Wanted</Link>
      <Link href="/swap">Swap</Link>
      <Link href="/demand">Demand</Link>
    </nav>
    <div className="header-actions"><Link className="btn btn-ghost" href="/login">Log in</Link><Link className="btn btn-primary" href="/register">Get Started</Link></div>
  </header>;
}
