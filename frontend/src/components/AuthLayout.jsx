import { Brand } from './AppLayout';
import Icon from './Icon';
import ServerWakeBanner from './ServerWakeBanner';

const HIGHLIGHTS = [
  { icon: 'search', text: 'Live job listings ranked against your resume' },
  { icon: 'target', text: 'Match scores with clear skill gaps' },
  { icon: 'sparkles', text: 'Tailored resume bullets grounded in your real experience' },
  { icon: 'mic', text: 'Interview questions and a live mock interviewer' },
];

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="auth-shell">
      <section className="auth-aside" aria-hidden="true">
        <Brand />
        <div className="auth-pitch">
          <h2>Your AI co-pilot for the job hunt.</h2>
          <ul>
            {HIGHLIGHTS.map((h) => (
              <li key={h.text}>
                <span className="pitch-icon"><Icon name={h.icon} size={16} /></span>
                {h.text}
              </li>
            ))}
          </ul>
        </div>
        <p className="auth-aside-foot">Free and open-source.</p>
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
