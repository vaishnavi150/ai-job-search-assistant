import { useState } from 'react';
import * as api from '../api';
import ChatWindow from '../components/ChatWindow';
import { Alert, Button, PageHeader } from '../components/ui';

const SUGGESTIONS = [
  'How should I explain a career gap?',
  'What should I highlight for a backend developer role?',
  'How do I negotiate a job offer?',
  'Give me a 30-second introduction based on my resume.',
];

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastFailed, setLastFailed] = useState(null);

  const send = async (text) => {
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setError('');
    setLastFailed(null);
    setLoading(true);
    try {
      const result = await api.sendChatMessage(text);
      setMessages((m) => [...m, { role: 'assistant', content: result.reply }]);
    } catch (err) {
      setError(err.message);
      setLastFailed(text);
      setMessages((m) => m.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Career chat"
        description="Ask about job searching, resumes, interviews or career moves. Answers use your resume when it’s relevant."
        actions={messages.length > 0 && (
          <Button variant="secondary" onClick={() => setMessages([])} disabled={loading}>New chat</Button>
        )}
      />
      <div className="card chat-card">
        <ChatWindow
          messages={messages}
          loading={loading}
          onSend={send}
          placeholder="Ask a question…"
          emptyState={(
            <div className="chat-empty">
              <p className="muted">Try one of these:</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" className="suggestion" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}
        />
        {error && (
          <Alert kind="error">
            {error}{' '}
            {lastFailed && <button type="button" className="link-btn" onClick={() => send(lastFailed)}>Retry</button>}
          </Alert>
        )}
      </div>
    </>
  );
}
