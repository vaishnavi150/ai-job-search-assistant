import { useState } from 'react';
import { Link } from 'react-router-dom';
import * as api from '../api';
import JobDescriptionInput, { jdProblem, useSharedJobDescription } from '../components/JobDescriptionInput';
import { Alert, Button, CopyButton, PageHeader } from '../components/ui';

export default function Interview() {
  const [jobDescription, setJobDescription] = useSharedJobDescription();
  const [numQuestions, setNumQuestions] = useState(5);
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    const problem = jdProblem(jobDescription);
    setError(problem);
    if (problem) return;
    setLoading(true);
    try {
      const result = await api.getInterviewQuestions(jobDescription.trim(), numQuestions);
      setQuestions(result.questions);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Interview questions"
        description="Get the technical and behavioural questions you’re likely to be asked for a role."
      />
      <div className="card">
        <JobDescriptionInput value={jobDescription} onChange={setJobDescription} />
        <div className="button-row">
          <label className="inline-field" htmlFor="num-q">
            <span>Questions</span>
            <select id="num-q" value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))}>
              {[3, 5, 8, 10, 15].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
          <Button onClick={generate} loading={loading} icon="sparkles">
            {loading ? 'Generating…' : 'Generate questions'}
          </Button>
        </div>
      </div>

      <Alert kind="error" onDismiss={error ? () => setError('') : undefined}>{error}</Alert>

      {questions.length > 0 && (
        <section className="card section" aria-live="polite">
          <div className="card-head">
            <h2 className="card-title">Practice questions</h2>
            <CopyButton text={questions.map((q, i) => `${i + 1}. ${q}`).join('\n')} label="Copy all" />
          </div>
          <ol className="question-list">
            {questions.map((q, i) => <li key={i}>{q}</li>)}
          </ol>
          <p className="muted small">
            Want to answer them out loud? Try a <Link to="/app/mock-interview" className="link">mock interview</Link>.
          </p>
        </section>
      )}
    </>
  );
}
