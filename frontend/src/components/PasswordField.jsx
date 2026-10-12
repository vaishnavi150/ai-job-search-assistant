import { useId, useState } from 'react';
import Icon from './Icon';
import { checkPassword } from '../utils/password';

export default function PasswordField({
  label = 'Password',
  value,
  onChange,
  autoComplete = 'current-password',
  showRules = false,
  error,
  id: idProp,
  ...props
}) {
  const generatedId = useId();
  const id = idProp || generatedId;
  const [visible, setVisible] = useState(false);
  const rules = showRules ? checkPassword(value) : [];
  const describedBy = [showRules && `${id}-rules`, error && `${id}-error`].filter(Boolean).join(' ') || undefined;

  return (
    <div className={`field ${error ? 'has-error' : ''}`}>
      <label htmlFor={id}>{label}</label>
      <div className="input-with-action">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          maxLength={128}
          {...props}
        />
        <button
          type="button"
          className="input-action"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
        >
          <Icon name={visible ? 'eyeOff' : 'eye'} size={18} />
        </button>
      </div>
      {showRules && (
        <ul className="password-rules" id={`${id}-rules`} aria-label="Password requirements">
          {rules.map((rule) => (
            <li key={rule.id} className={rule.met ? 'met' : ''}>
              <Icon name={rule.met ? 'check' : 'x'} size={14} />
              <span>{rule.label}</span>
              <span className="sr-only">{rule.met ? '(met)' : '(not met)'}</span>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </div>
  );
}
