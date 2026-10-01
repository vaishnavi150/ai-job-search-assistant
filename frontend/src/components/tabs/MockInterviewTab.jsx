import { useState } from 'react';
import * as api from '../../api';

export default function MockInterviewTab() {
  const [jobDescription, setJobDescription] = useState('');
  const [started, setStarted] = useState(false);
  const [history, setHistory] = useState([]); // [{role, content}]
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const start = async () => {
    if (!jobDescription) return;
    setError('');
    setLoading(true);
    try {
      const result = await api.mockInterviewReply(jobDescription, []);
      setHistory([{ role: 'assistant', content: result.reply }]);
      setStarted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sendAnswer = async () => {
    if (!input.trim()) return;
    const newHistory = [...history, { role: 'user', content: input }];
    setHistory(newHistory);
    setInput('');
    setError('');
    setLoading(true);
    try {
      const result = await api.mockInterviewReply(jobDescription, newHistory);
      setHistory([...newHistory, { role: 'assistant', content: result.reply }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStarted(false);
    setHistory([]);
    setInput('');
  };

  return (
    <div className="tab-panel">
      <h2>🎤 Mock Interview</h2>
      <p className="hint">A live back-and-forth: the AI interviewer asks a question, you answer, it gives
        feedback and asks the next one.</p>

      {!started ? (
        <>
          <textarea
            placeholder="Paste job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={8}
          />
          <button onClick={start} disabled={!jobDescription || loading}>
            {loading ? 'Starting...' : 'Start mock interview'}
          </button>
        </>
      ) : (
        <>
          <div className="chat-window">
            {history.map((turn, i) => (
              <div key={i} className={`chat-bubble ${turn.role}`}>{turn.content}</div>
            ))}
            {loading && <div className="chat-bubble assistant">Thinking...</div>}
          </div>
          <div className="chat-input-row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendAnswer()}
              placeholder="Type your answer..."
              disabled={loading}
            />
            <button onClick={sendAnswer} disabled={loading || !input.trim()}>Send</button>
          </div>
          <button className="btn-link" onClick={reset}>End interview / start over</button>
        </>
      )}
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
