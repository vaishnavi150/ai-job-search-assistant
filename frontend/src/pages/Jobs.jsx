import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as api from '../api';
import Icon from '../components/Icon';
import { Alert, Button, EmptyState, PageHeader, Spinner } from '../components/ui';

function relevanceLabel(r) {
  if (r == null) return null;
  if (r >= 0.7) return { text: 'Great fit', tone: 'good' };
  if (r >= 0.5) return { text: 'Good fit', tone: 'ok' };
  return { text: 'Possible fit', tone: 'low' };
}

function JobCard({ job, onMatch, onSave, saveState }) {
  const fit = relevanceLabel(job.relevance);
  const [open, setOpen] = useState(false);
  return (
    <article className="job-card">
      <div className="job-head">
        <div>
          <h3 className="job-title">{job.title}</h3>
          <p className="job-company">{job.company}</p>
        </div>
        {fit && (
          <span className={`fit-badge fit-${fit.tone}`} title={`Resume relevance ${Math.round(job.relevance * 100)}%`}>
            {fit.text} · {Math.round(job.relevance * 100)}%
          </span>
        )}
      </div>
      <ul className="job-meta">
        <li><Icon name="mapPin" size={14} />{job.location}</li>
        {job.job_type && <li><Icon name="briefcase" size={14} />{job.job_type}</li>}
        {job.salary && <li>{job.salary}</li>}
        {job.posted_at && <li>Posted {job.posted_at}</li>}
      </ul>
      {job.tags.length > 0 && (
        <div className="chip-row">
          {job.tags.slice(0, 6).map((t) => <span key={t} className="chip">{t}</span>)}
        </div>
      )}
      <p className="job-snippet">{open ? job.description : job.snippet}</p>
      {job.description.length > job.snippet.length && (
        <button type="button" className="link-btn" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
          {open ? 'Show less' : 'Read more'}
        </button>
      )}
      <div className="job-actions">
        <a className="btn btn-secondary" href={job.url} target="_blank" rel="noopener noreferrer">
          <Icon name="external" size={16} /><span>View on {job.source}</span>
        </a>
        <Button variant="secondary" icon="target" onClick={() => onMatch(job)}>Check match</Button>
        <Button
          variant="ghost"
          icon={saveState === 'saved' ? 'check' : 'plus'}
          loading={saveState === 'saving'}
          disabled={saveState === 'saved'}
          onClick={() => onSave(job)}
        >
          {saveState === 'saved' ? 'Saved' : 'Save to tracker'}
        </Button>
      </div>
    </article>
  );
}

export default function Jobs() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saveStates, setSaveStates] = useState({});

  const search = async (e) => {
    e.preventDefault();
    if (query.trim().length < 2) {
      setError('Enter at least 2 characters to search, e.g. “python developer”.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      setResult(await api.searchJobs({ q: query.trim(), location: location.trim(), remoteOnly }));
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const onMatch = (job) => {
    navigate('/app/match', {
      state: {
        jobDescription: `${job.title} at ${job.company}\n\n${job.description}`,
        company: job.company,
        jobTitle: job.title,
        jobUrl: job.url,
      },
    });
  };

  const onSave = async (job) => {
    setSaveStates((s) => ({ ...s, [job.id]: 'saving' }));
    try {
      await api.createApplication({
        company: job.company.slice(0, 200),
        job_title: job.title.slice(0, 200),
        job_url: job.url,
        job_description: job.description.slice(0, 20000),
        match_score: job.relevance ?? null,
        status: 'saved',
      });
      setSaveStates((s) => ({ ...s, [job.id]: 'saved' }));
    } catch (err) {
      setSaveStates((s) => ({ ...s, [job.id]: undefined }));
      setError(err.message);
    }
  };

  return (
    <>
      <PageHeader
        title="Find jobs"
        description="Search live listings. With a resume uploaded, results are ranked by how well they fit you."
      />

      <form className="card search-form" onSubmit={search} role="search">
        <div className="search-fields">
          <div className="field grow">
            <label htmlFor="job-q">Keywords</label>
            <input
              id="job-q"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. python backend, data analyst"
              maxLength={100}
            />
          </div>
          <div className="field">
            <label htmlFor="job-loc">Location <span className="optional">(optional)</span></label>
            <input
              id="job-loc"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. India, Berlin"
              maxLength={60}
            />
          </div>
        </div>
        <div className="search-foot">
          <label className="toggle">
            <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} />
            <span>Remote only</span>
          </label>
          <Button type="submit" loading={loading} icon="search">{loading ? 'Searching…' : 'Search jobs'}</Button>
        </div>
      </form>

      <Alert kind="error" onDismiss={error ? () => setError('') : undefined}>{error}</Alert>

      {loading && <div className="section"><Spinner label="Searching job boards…" /></div>}

      {!loading && result && (
        <section className="section" aria-live="polite">
          <div className="results-meta">
            <span>
              {result.jobs.length} result{result.jobs.length === 1 ? '' : 's'}
              {result.ranked_by_resume ? ' · ranked by resume fit' : ''}
            </span>
            <span className="muted small">Listings from {result.sources.join(' and ')}</span>
          </div>
          {result.unavailable_sources.length > 0 && (
            <Alert kind="warning">
              {result.unavailable_sources.join(', ')} couldn’t be reached, so results may be incomplete.
            </Alert>
          )}
          {!result.ranked_by_resume && result.jobs.length > 0 && (
            <Alert kind="info">
              <Link to="/app/resume" className="link">Upload your resume</Link> to rank these jobs by how well they fit you.
            </Alert>
          )}
          {result.jobs.length === 0 ? (
            <EmptyState icon="search" title="No matching jobs">
              Try broader keywords (e.g. “developer” instead of a specific framework), or remove the location filter.
            </EmptyState>
          ) : (
            <div className="job-list">
              {result.jobs.map((job) => (
                <JobCard key={job.id} job={job} onMatch={onMatch} onSave={onSave} saveState={saveStates[job.id]} />
              ))}
            </div>
          )}
        </section>
      )}

      {!loading && !result && !error && (
        <EmptyState icon="search" title="Search remote and international roles">
          Results come from free public job boards (Remotive and Arbeitnow) and refresh every few hours.
        </EmptyState>
      )}
    </>
  );
}
