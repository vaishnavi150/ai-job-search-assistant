import { useState } from 'react';
import * as api from '../api';
import ChatWindow from '../components/ChatWindow';
import JobDescriptionInput, { jdProblem, useSharedJobDescription } from '../components/JobDescriptionInput';
import { Alert, Button, PageHeader } from '../components/ui';

// The server caps history at 40 turns; end gracefully before hitting it.
const MAX_TURNS = 36;

export default function MockInterview() {
  const [jobDescription, setJobDescription] = useSharedJobDescription();
  const [started, setStarted] = useState(false);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastFailed, setLastFailed] = useState(null);

  const start = async () => {
    const problem = jdProblem(jobDescription);
    setError(problem);
    if (problem) return;
    setLoading(true);
    try {
      const result = await api.mockInterviewReply(jobDescription.trim(), []);
      setHistory([{ role: 'assistant', content: result.reply }]);
      setStarted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const send = async (text, base = history) => {
    const next = [...base, { role: 'user', content: text }];
    setHistory(next);
    setError('');
    setLastFailed(null);
    setLoading(true);
    try {
      const result = await api.mockInterviewReply(jobDescription.trim(), next);
      setHistory([...next, { role: 'assistant', content: result.reply }]);
    } catch (err) {
      setError(err.message);
      setHistory(base);
      setLastFailed(text);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStarted(false);
    setHistory([]);
    setError('');
    setLastFailed(null);
  };

  const atLimit = history.length >= MAX_TURNS;

  return (
    <>
      <PageHeader
        title="Mock interview"
        description="An AI interviewer asks one question at a time and gives feedback on each answer."
        actions={started && <Button variant="secondary" onClick={reset}>End interview</Button>}
      />

      {!started ? (
        <div className="card">
          <JobDescriptionInput value={jobDescription} onChange={setJobDescription} />
          <Alert kind="error">{error}</Alert>
          <Button onClick={start} loading={loading} icon="mic">{loading ? 'Starting…' : 'Start mock interview'}</Button>
        </div>
      ) : (
        <div className="card chat-card">
          <ChatWindow
            messages={history}
            loading={loading}
            onSend={(text) => send(text)}
            placeholder={atLimit ? 'Interview complete - start a new one to keep practising.' : 'Type your answer…'}
            disabled={atLimit}
            inputLabel="Your answer"
          />
          {error && (
            <Alert kind="error">
              {error}{' '}
              {lastFailed && (
                <button type="button" className="link-btn" onClick={() => send(lastFailed)}>Retry</button>
              )}
            </Alert>
          )}
          {atLimit && <Alert kind="info">That’s a full interview. Start a new one to practise again.</Alert>}
        </div>
      )}
    </>
  );
}
