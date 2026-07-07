import Link from 'next/link';
import type { PropsWithChildren } from 'react';
import { useAuth } from '../context/AuthContext';

export function SiteFrame({ children }: PropsWithChildren) {
  const { user, signOutUser } = useAuth();

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

        <div className="topbar__actions">
          {user ? (
            <>
              <Link href="/account" className="button button--ghost topbar__button">
                Account
              </Link>
              <button
                type="button"
                className="button button--secondary topbar__button"
                onClick={async () => {
                  await signOutUser();
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="button button--ghost topbar__button">
                Sign in
              </Link>
              <Link href="/signup" className="button button--secondary topbar__button">
                Create account
              </Link>
            </>
          )}
        </div>
      </header>

      <main>{children}</main>

    </div>
  );
}