'use client';

import { useEffect } from 'react';

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-form">
          <div className="eyebrow">CAMPUSCART</div>
          <h2>Something went wrong.</h2>
          <p className="muted">The page failed to load. Your session and saved marketplace data are unchanged.</p>
          <button className="btn btn-primary full" onClick={() => reset()}>Try again</button>
        </div>
      </div>
    </main>
  );
}
