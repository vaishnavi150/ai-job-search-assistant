import { useState } from 'react';
import * as api from '../../api';

export default function InterviewTab() {
  const [jobDescription, setJobDescription] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setError('');
    setLoading(true);
    try {
      const result = await api.getInterviewQuestions(jobDescription, numQuestions);
      setQuestions(result.questions);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-panel">
      <h2>💬 Interview Questions</h2>
      <p className="hint">Generate likely interview questions from a job description to practice ahead of time.</p>
      <textarea
        placeholder="Paste job description here..."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        rows={8}
      />
      <div className="button-row">
        <label className="inline-label">
          Number of questions:
          <input type="number" min={3} max={10} value={numQuestions}
                 onChange={(e) => setNumQuestions(Number(e.target.value))} />
        </label>
        <button onClick={generate} disabled={!jobDescription || loading}>
          {loading ? 'Generating...' : 'Generate questions'}
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
      {questions.length > 0 && (
        <div className="result-card">
          <ol>{questions.map((q, i) => <li key={i}>{q}</li>)}</ol>
        </div>
      )}
    </div>
  );
}
