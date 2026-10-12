import { useEffect } from 'react';
import { Brand } from './Logo';
import Icon from './Icon';
import ServerWakeBanner from './ServerWakeBanner';

const HIGHLIGHTS = [
  { icon: 'search', text: 'Live job listings ranked against your resume' },
  { icon: 'target', text: 'Match scores with clear skill gaps' },
  { icon: 'sparkles', text: 'Tailored resume bullets grounded in your real experience' },
  { icon: 'mic', text: 'Interview questions and a live mock interviewer' },
];

export default function AuthLayout({ title, subtitle, children }) {
  useEffect(() => {
    document.title = `${title} · Nextrung`;
  }, [title]);

  return (
    <div className="auth-shell">
      <section className="auth-aside" aria-hidden="true">
        <Brand />
        <div className="auth-pitch">
          <p className="auth-eyebrow">AI career assistant</p>
          <h2>Climb to your next role, one rung at a time.</h2>
          <ul>
            {HIGHLIGHTS.map((h) => (
              <li key={h.text}>
                <span className="pitch-icon"><Icon name={h.icon} size={16} /></span>
                {h.text}
              </li>
            ))}
          </ul>
        </div>
        <p className="auth-aside-foot">© Nextrung · Free to use</p>
      </section>
      <main className="auth-main">
        <ServerWakeBanner />
        <div className="auth-card">
          <div className="auth-card-brand"><Brand /></div>
          <h1>{title}</h1>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
        </div>
      </main>
    </div>
  );
}
