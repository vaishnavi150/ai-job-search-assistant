import { useState } from 'react';
import * as api from '../../api';

export default function ChatTab() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const send = async () => {
    if (!input.trim()) return;
    const message = input;
    setHistory((h) => [...h, { role: 'user', content: message }]);
    setInput('');
    setError('');
    setLoading(true);
    try {
      const result = await api.sendChatMessage(message);
      setHistory((h) => [...h, { role: 'assistant', content: result.reply }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-panel">
      <h2>🤖 AI Career Assistant</h2>
      <p className="hint">Ask anything about your job search - it grounds answers in your uploaded resume when relevant.</p>
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
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="e.g. How should I explain a career gap?"
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>Send</button>
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
