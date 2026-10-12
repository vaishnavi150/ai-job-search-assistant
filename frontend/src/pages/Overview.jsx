import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import * as api from '../api';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import { Alert, PageHeader, Spinner, StatusBadge, STATUS_LABELS } from '../components/ui';

const QUICK_ACTIONS = [
  { to: '/app/jobs', icon: 'search', title: 'Find jobs', text: 'Search live listings ranked against your resume.' },
  { to: '/app/match', icon: 'target', title: 'Match & tailor', text: 'Score a job post and get tailored bullets.' },
  { to: '/app/mock-interview', icon: 'mic', title: 'Mock interview', text: 'Practise with an AI interviewer.' },
  { to: '/app/chat', icon: 'chat', title: 'Career chat', text: 'Ask anything about your job search.' },
];

export default function Overview() {
  const { email } = useAuth();
  const [resume, setResume] = useState(undefined); // undefined = loading, null = none
  const [applications, setApplications] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getMyResume()
      .then(setResume)
      .catch((err) => (err.status === 404 ? setResume(null) : setError(err.message)));
    api.listApplications()
      .then(setApplications)
      .catch((err) => setError(err.message));
  }, []);

  const counts = Object.fromEntries(Object.keys(STATUS_LABELS).map((s) => [s, 0]));
  applications?.forEach((a) => {
    counts[a.status] = (counts[a.status] || 0) + 1;
  });
  const active = (counts.applied || 0) + (counts.interviewing || 0);
  const name = email?.split('@')[0];

  return (
    <>
      <PageHeader title={`Welcome back${name ? `, ${name}` : ''}`} description="Here’s where your job search stands." />
      <Alert kind="error">{error}</Alert>

      {resume === null && (
        <div className="callout">
          <div className="callout-icon"><Icon name="upload" size={20} /></div>
          <div>
            <h3>Start by uploading your resume</h3>
            <p>Matching, job ranking, tailored bullets and chat all use it to give advice specific to you.</p>
          </div>
          <Link to="/app/resume" className="btn btn-primary">Upload resume</Link>
        </div>
      )}

      <section className="stat-grid" aria-label="Summary">
        <div className="stat-card">
          <span className="stat-label">Resume</span>
          {resume === undefined ? <Spinner size="sm" /> : (
            <strong className="stat-value stat-text">{resume ? 'Uploaded' : 'Missing'}</strong>
          )}
          <span className="stat-sub">{resume ? resume.filename : 'PDF, DOCX or TXT'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Tracked jobs</span>
          {applications === null ? <Spinner size="sm" /> : <strong className="stat-value">{applications.length}</strong>}
          <span className="stat-sub">{counts.saved} saved</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">In progress</span>
          {applications === null ? <Spinner size="sm" /> : <strong className="stat-value">{active}</strong>}
          <span className="stat-sub">{counts.interviewing} interviewing</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Offers</span>
          {applications === null ? <Spinner size="sm" /> : <strong className="stat-value">{counts.offer}</strong>}
          <span className="stat-sub">{counts.rejected} closed</span>
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">Quick actions</h2>
        <div className="action-grid">
          {QUICK_ACTIONS.map((a) => (
            <Link key={a.to} to={a.to} className="action-card">
              <span className="action-icon"><Icon name={a.icon} size={20} /></span>
              <span className="action-title">{a.title}</span>
              <span className="action-text">{a.text}</span>
              <Icon name="arrowRight" size={16} className="action-arrow" />
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2 className="section-title">Recent applications</h2>
          <Link to="/app/applications" className="link">View all</Link>
        </div>
        {applications === null ? (
          <Spinner label="Loading…" />
        ) : applications.length === 0 ? (
          <div className="card muted-card">
            No applications yet. Save jobs from <Link to="/app/jobs" className="link">Find jobs</Link> or add them on the{' '}
            <Link to="/app/applications" className="link">Applications</Link> page.
          </div>
        ) : (
          <ul className="card list-card">
            {applications.slice(0, 5).map((a) => (
              <li key={a.id} className="list-row">
                <div className="list-main">
                  <strong>{a.job_title}</strong>
                  <span className="muted">{a.company}</span>
                </div>
                {a.match_score != null && <span className="muted small">{Math.round(a.match_score * 100)}% match</span>}
                <StatusBadge status={a.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
