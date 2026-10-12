import { useEffect, useRef, useState } from 'react';
import Icon from './Icon';

export default function ChatWindow({ messages, loading, onSend, placeholder, disabled, emptyState, inputLabel = 'Message' }) {
  const [input, setInput] = useState('');
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, loading]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus({ preventScroll: true });
  }, [loading]);

  const submit = (e) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading || disabled) return;
    setInput('');
    onSend(text);
  };

  const onKeyDown = (e) => {
    // Enter sends, Shift+Enter adds a line; ignore Enter while an IME is composing.
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat">
      <div className="chat-log" role="log" aria-live="polite" aria-relevant="additions">
        {messages.length === 0 && !loading && emptyState}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-${m.role}`}>
            <span className="chat-author">{m.role === 'user' ? 'You' : 'AI'}</span>
            <div className="chat-bubble">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-assistant">
            <span className="chat-author">AI</span>
            <div className="chat-bubble typing" aria-label="AI is typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <form className="chat-composer" onSubmit={submit}>
        <label htmlFor="chat-input" className="sr-only">{inputLabel}</label>
        <textarea
          id="chat-input"
          ref={inputRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          maxLength={4000}
        />
        <button type="submit" className="btn btn-primary btn-icon" disabled={!input.trim() || loading || disabled} aria-label="Send">
          <Icon name="send" size={18} />
        </button>
      </form>
      <p className="chat-hint">Press Enter to send · Shift + Enter for a new line</p>
    </div>
  );
}
