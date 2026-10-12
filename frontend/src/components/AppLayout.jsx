import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Icon from './Icon';
import ServerWakeBanner from './ServerWakeBanner';

export const NAV_ITEMS = [
  { to: '/app', label: 'Overview', icon: 'home', end: true },
  { to: '/app/resume', label: 'Resume', icon: 'file' },
  { to: '/app/jobs', label: 'Find jobs', icon: 'search' },
  { to: '/app/match', label: 'Match & tailor', icon: 'target' },
  { to: '/app/interview', label: 'Interview questions', icon: 'help' },
  { to: '/app/mock-interview', label: 'Mock interview', icon: 'mic' },
  { to: '/app/applications', label: 'Applications', icon: 'briefcase' },
  { to: '/app/chat', label: 'Career chat', icon: 'chat' },
];

export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        <Icon name="sparkles" size={16} />
      </span>
      <span className="brand-name">AI Job Search <span className="brand-ai">Assistant</span></span>
    </span>
  );
}

export default function AppLayout() {
  const { email, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  // Close the mobile drawer on navigation, and focus the page for screen readers.
  useEffect(() => {
    setMenuOpen(false);
    document.getElementById('main-content')?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onKey = (e) => e.key === 'Escape' && setMenuOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to content</a>

      <header className="mobile-topbar">
        <button
          type="button"
          className="icon-btn"
          onClick={() => setMenuOpen(true)}
          aria-label="Open navigation"
          aria-expanded={menuOpen}
          aria-controls="sidebar"
        >
          <Icon name="menu" size={22} />
        </button>
        <Brand />
        <span style={{ width: 36 }} />
      </header>

      {menuOpen && <div className="sidebar-backdrop" onClick={() => setMenuOpen(false)} aria-hidden="true" />}

      <aside id="sidebar" className={`sidebar ${menuOpen ? 'open' : ''}`} aria-label="Main navigation">
        <div className="sidebar-head">
          <Brand />
          <button type="button" className="icon-btn sidebar-close" onClick={() => setMenuOpen(false)} aria-label="Close navigation">
            <Icon name="close" size={20} />
          </button>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className="nav-link">
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <NavLink to="/app/account" className="nav-link account-link">
            <span className="avatar" aria-hidden="true">{email?.[0]?.toUpperCase() ?? '?'}</span>
            <span className="account-email" title={email}>{email}</span>
          </NavLink>
          <button type="button" className="nav-link logout-btn" onClick={logout}>
            <Icon name="logout" size={18} />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      <div className="app-main">
        <ServerWakeBanner />
        <main id="main-content" className="page" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
