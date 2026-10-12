import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import * as api from '../api';
import JobDescriptionInput, { jdProblem, useSharedJobDescription } from '../components/JobDescriptionInput';
import { Alert, Button, CopyButton, Field, PageHeader, ScoreRing } from '../components/ui';

export default function Match() {
  const { state } = useLocation();
  const [jobDescription, setJobDescription] = useSharedJobDescription(state?.jobDescription);
  const [company, setCompany] = useState(state?.company ?? '');
  const [jobTitle, setJobTitle] = useState(state?.jobTitle ?? '');
  const [jobUrl, setJobUrl] = useState(state?.jobUrl ?? null);
  const [linkedDescription] = useState(state?.jobDescription ?? null);
  const [match, setMatch] = useState(null);
  const [bullets, setBullets] = useState(null);
  const [error, setError] = useState('');
  const [needsResume, setNeedsResume] = useState(false);
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [loadingBullets, setLoadingBullets] = useState(false);
  const [saveState, setSaveState] = useState('');

  const changeDescription = (value) => {
    setJobDescription(value);
    // Its first line is "<title> at <company>"; small edits below it keep the link.
    const firstLine = (text) => text.split('\n', 1)[0].trim();
    if (jobUrl && linkedDescription && firstLine(value) !== firstLine(linkedDescription)) setJobUrl(null);
  };

  const check = () => {
    const problem = jdProblem(jobDescription);
    setError(problem);
    setNeedsResume(false);
    return !problem;
  };

  const handleError = (err) => {
    setNeedsResume(/upload (a|one)|no resume/i.test(err.message));
    setError(err.message);
  };

  const runMatch = async () => {
    if (!check()) return;
    setLoadingMatch(true);
    try {
      setMatch(await api.matchResume(jobDescription.trim()));
      setSaveState('');
    } catch (err) {
      handleError(err);
    } finally {
      setLoadingMatch(false);
    }
  };

  const runBullets = async () => {
    if (!check()) return;
    setLoadingBullets(true);
    try {
      setBullets(await api.tailorBullets(jobDescription.trim()));
    } catch (err) {
      handleError(err);
    } finally {
      setLoadingBullets(false);
    }
  };

  const save = async () => {
    if (!company.trim() || !jobTitle.trim()) {
      setError('Add the company and job title to save this job to your tracker.');
      return;
    }
    setSaveState('saving');
    setError('');
    try {
      await api.createApplication({
        company: company.trim(),
        job_title: jobTitle.trim(),
        job_description: jobDescription.trim().slice(0, 20000),
        job_url: jobUrl,
        match_score: match?.match_score ?? null,
        status: 'saved',
      });
      setSaveState('saved');
    } catch (err) {
      setSaveState('');
      setError(err.message);
    }
  };

  return (
    <>
      <PageHeader
        title="Match & tailor"
        description="See how well your resume fits a job, what’s missing, and get bullet points rewritten for it."
      />

      <div className="card">
        <JobDescriptionInput value={jobDescription} onChange={changeDescription} />
        <div className="button-row">
          <Button onClick={runMatch} loading={loadingMatch} icon="target">
            {loadingMatch ? 'Scoring…' : 'Calculate match'}
          </Button>
          <Button variant="secondary" onClick={runBullets} loading={loadingBullets} icon="sparkles">
            {loadingBullets ? 'Writing…' : 'Tailor resume bullets'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert kind="error" onDismiss={() => setError('')}>
          {error}
          {needsResume && <> <Link to="/app/resume" className="link">Upload your resume</Link></>}
        </Alert>
      )}

      {match && (
        <section className="card section" aria-live="polite">
          <div className="match-summary">
            <ScoreRing value={match.match_score} label="match" size={112} />
            <div className="match-text">
              <h2 className="card-title">{match.summary.split(' - ')[0].split('.')[0]}</h2>
              <p className="muted">{match.summary}</p>
              <dl className="breakdown">
                <div><dt>Experience similarity</dt><dd>{Math.round(match.semantic_score * 100)}%</dd></div>
                <div>
                  <dt>Skills covered</dt>
                  <dd>{match.skill_coverage == null ? 'n/a' : `${Math.round(match.skill_coverage * 100)}%`}</dd>
                </div>
              </dl>
            </div>
          </div>
          <div className="skills-columns">
            <div>
              <h3 className="sub-title">Skills you have</h3>
              <div className="chip-row">
                {match.matched_skills.length ? match.matched_skills.map((s) => <span key={s} className="chip chip-good">{s}</span>)
                  : <span className="muted small">No listed skills detected in both.</span>}
              </div>
            </div>
            <div>
              <h3 className="sub-title">Skills to add or highlight</h3>
              <div className="chip-row">
                {match.missing_skills.length ? match.missing_skills.map((s) => <span key={s} className="chip chip-warn">{s}</span>)
                  : <span className="muted small">None detected - nice.</span>}
              </div>
            </div>
          </div>

          <div className="save-row">
            <h3 className="sub-title">Save to your tracker</h3>
            <div className="save-fields">
              <Field label="Company" htmlFor="save-company">
                <input id="save-company" value={company} onChange={(e) => setCompany(e.target.value)} maxLength={200} />
              </Field>
              <Field label="Job title" htmlFor="save-title">
                <input id="save-title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} maxLength={200} />
              </Field>
              <Button
                variant="secondary"
                icon={saveState === 'saved' ? 'check' : 'plus'}
                loading={saveState === 'saving'}
                disabled={saveState === 'saved'}
                onClick={save}
              >
                {saveState === 'saved' ? 'Saved' : 'Save with score'}
              </Button>
            </div>
            {saveState === 'saved' && (
              <p className="small">Saved. <Link to="/app/applications" className="link">Open tracker</Link></p>
            )}
          </div>
        </section>
      )}

      {bullets && (
        <section className="card section" aria-live="polite">
          <div className="card-head">
            <h2 className="card-title">Tailored resume bullets</h2>
            <CopyButton text={bullets.bullets.map((b) => `• ${b}`).join('\n')} label="Copy all" />
          </div>
          <p className="muted small">Written only from your resume - review them before using.</p>
          <ul className="bullet-list">
            {bullets.bullets.map((b, i) => (
              <li key={i}>
                <span>{b}</span>
                <CopyButton text={b} />
              </li>
            ))}
          </ul>
          {bullets.grounded_on?.length > 0 && (
            <details className="details">
              <summary>Resume excerpts these are based on</summary>
              <ul>{bullets.grounded_on.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </details>
          )}
        </section>
      )}
    </>
  );
}
