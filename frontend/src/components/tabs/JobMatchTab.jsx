import { useState } from 'react';
import * as api from '../../api';

export default function JobMatchTab() {
  const [jobDescription, setJobDescription] = useState('');
  const [match, setMatch] = useState(null);
  const [bullets, setBullets] = useState(null);
  const [error, setError] = useState('');
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [loadingBullets, setLoadingBullets] = useState(false);

  const runMatch = async () => {
    setError('');
    setLoadingMatch(true);
    try {
      const result = await api.matchResume(jobDescription);
      setMatch(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingMatch(false);
    }
  };

  const runBullets = async () => {
    setError('');
    setLoadingBullets(true);
    try {
      const result = await api.tailorBullets(jobDescription);
      setBullets(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingBullets(false);
    }
  };

  return (
    <div className="tab-panel">
      <h2>🎯 Job Match & Tailoring</h2>
      <p className="hint">Paste a job description to score your resume against it, see missing skills,
        and generate tailored bullet points (grounded only in your actual resume).</p>

      <textarea
        placeholder="Paste job description here..."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        rows={8}
      />
      <div className="button-row">
        <button onClick={runMatch} disabled={!jobDescription || loadingMatch}>
          {loadingMatch ? 'Scoring...' : '🔍 Calculate match'}
        </button>
        <button onClick={runBullets} disabled={!jobDescription || loadingBullets}>
          {loadingBullets ? 'Generating...' : '✍️ Generate tailored bullets'}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {match && (
        <div className="result-card">
          <h3>Match score: {(match.match_score * 100).toFixed(0)}%</h3>
          <div className="skills-row">
            <div>
              <strong>✅ Matched skills</strong>
              <ul>{match.matched_skills.length ? match.matched_skills.map((s) => <li key={s}>{s}</li>) : <li>None detected</li>}</ul>
            </div>
            <div>
              <strong>⚠️ Missing skills</strong>
              <ul>{match.missing_skills.length ? match.missing_skills.map((s) => <li key={s}>{s}</li>) : <li>None - great fit!</li>}</ul>
            </div>
          </div>
        </div>
      )}

      {bullets && (
        <div className="result-card">
          <h3>Tailored bullet points</h3>
          <ul>{bullets.bullets.map((b, i) => <li key={i}>{b}</li>)}</ul>
          {bullets.grounded_on?.length > 0 && (
            <details>
              <summary>Grounded on these resume excerpts</summary>
              <ul>{bullets.grounded_on.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
