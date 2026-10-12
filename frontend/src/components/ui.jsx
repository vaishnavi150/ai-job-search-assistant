import { useState } from 'react';
import Icon from './Icon';

export function Alert({ kind = 'error', children, onDismiss }) {
  if (!children) return null;
  const icon = { error: 'alert', success: 'check', info: 'info', warning: 'alert' }[kind];
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <Icon name={icon} size={18} />
      <div className="alert-body">{children}</div>
      {onDismiss && (
        <button type="button" className="icon-btn" onClick={onDismiss} aria-label="Dismiss">
          <Icon name="close" size={16} />
        </button>
      )}
    </div>
  );
}

export function Spinner({ label, size = 'md' }) {
  return (
    <span className={`spinner-wrap spinner-${size}`} role="status">
      <span className="spinner" aria-hidden="true" />
      {label ? <span>{label}</span> : <span className="sr-only">Loading</span>}
    </span>
  );
}

export function Button({ loading, children, variant = 'primary', className = '', icon, ...props }) {
  return (
    <button className={`btn btn-${variant} ${className}`} disabled={loading || props.disabled} {...props}>
      {loading ? <span className="spinner spinner-inline" aria-hidden="true" /> : icon && <Icon name={icon} size={16} />}
      <span>{children}</span>
    </button>
  );
}

export function PageHeader({ title, description, actions }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function EmptyState({ icon = 'info', title, children, action }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Icon name={icon} size={22} />
      </div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function CopyButton({ text, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard blocked - nothing useful to do
    }
  };
  return (
    <button type="button" className="btn btn-ghost btn-sm" onClick={copy} aria-live="polite">
      <Icon name={copied ? 'check' : 'copy'} size={14} />
      <span>{copied ? 'Copied' : label}</span>
    </button>
  );
}

export function Field({ label, htmlFor, hint, error, children, optional }) {
  return (
    <div className={`field ${error ? 'has-error' : ''}`}>
      {label && (
        <label htmlFor={htmlFor}>
          {label} {optional && <span className="optional">(optional)</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="field-hint" id={`${htmlFor}-hint`}>{hint}</p>}
      {error && <p className="field-error" id={`${htmlFor}-error`}>{error}</p>}
    </div>
  );
}

export function ScoreRing({ value, size = 96, label }) {
  const pct = Math.round((value ?? 0) * 100);
  const tone = pct >= 75 ? 'good' : pct >= 50 ? 'ok' : 'low';
  const r = 42;
  const c = 2 * Math.PI * r;
  return (
    <div className={`score-ring score-${tone}`} style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r={r} className="score-track" />
        <circle
          cx="50" cy="50" r={r}
          className="score-value"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct / 100)}
        />
      </svg>
      <div className="score-label">
        <strong>{pct}%</strong>
        {label && <span>{label}</span>}
      </div>
    </div>
  );
}

export const STATUS_LABELS = {
  saved: 'Saved',
  applied: 'Applied',
  interviewing: 'Interviewing',
  offer: 'Offer',
  rejected: 'Rejected',
};

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}
