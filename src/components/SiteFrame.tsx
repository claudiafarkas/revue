import { Link, NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

const navItems = [
  { label: 'Get Started', href: '/' },
  { label: 'Job Postings', href: '/postings' },
  { label: 'Resume', href: '/resume' },
  { label: 'Processing', href: '/processing' },
  { label: 'Report', href: '/report' },
];

export function SiteFrame({ children }: PropsWithChildren) {
  return (
    <div className="site-shell">
      <div className="site-aura" aria-hidden="true" />
      <header className="topbar">
        <Link to="/" className="brandmark" aria-label="Revue.ai home">
          <span className="brandmark__monogram">R</span>
          <span>
            Revue.ai
            <small>Your Career, Thoughtfully Reviewed.</small>
          </span>
        </Link>

        <nav className="topnav" aria-label="Primary navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                isActive ? 'topnav__link topnav__link--active' : 'topnav__link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main>{children}</main>

      <footer className="footer-note">
        <p>UI prototype for the Revue.ai workflow. Backend integration comes next.</p>
      </footer>
    </div>
  );
}