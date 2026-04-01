import Link from 'next/link';
import type { PropsWithChildren } from 'react';

export function SiteFrame({ children }: PropsWithChildren) {
  return (
    <div className="site-shell">
      <div className="site-aura" aria-hidden="true" />
      <header className="topbar">
        <Link href="/" className="brandmark" aria-label="Revue.ai home">
          <span className="brandmark__monogram">R</span>
          <span>
            Revue.ai
            <small>Your Career, Thoughtfully Reviewed.</small>
          </span>
        </Link>
      </header>

      <main>{children}</main>

    </div>
  );
}