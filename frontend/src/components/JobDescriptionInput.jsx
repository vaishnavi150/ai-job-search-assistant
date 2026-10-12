import { useEffect, useState } from 'react';
import { Field } from './ui';

const KEY = 'jobDescription';
export const MIN_JD_LENGTH = 30;
export const MAX_JD_LENGTH = 20000;

// The same job description is used by Match, Interview questions and Mock
// interview; keep it for the browser session so users don't re-paste it.
export function useSharedJobDescription(initial) {
  const [value, setValue] = useState(() => {
    if (initial) return initial;
    try {
      return sessionStorage.getItem(KEY) || '';
    } catch {
      return '';
    }
  });
  useEffect(() => {
    try {
      sessionStorage.setItem(KEY, value);
    } catch {
      // storage unavailable - fine, it just won't persist
    }
  }, [value]);
  return [value, setValue];
}

export function jdProblem(value) {
  const len = value.trim().length;
  if (len === 0) return 'Paste a job description first.';
  if (len < MIN_JD_LENGTH) return `Add a bit more detail (at least ${MIN_JD_LENGTH} characters).`;
  return '';
}

export default function JobDescriptionInput({ value, onChange, id = 'job-description', rows = 9 }) {
  const len = value.trim().length;
  return (
    <Field label="Job description" htmlFor={id}>
      <textarea
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        maxLength={MAX_JD_LENGTH}
        placeholder="Paste the full job posting - responsibilities, requirements, and nice-to-haves."
        aria-describedby={`${id}-count`}
      />
      <div className="textarea-meta" id={`${id}-count`}>
        <span>{len > 0 && len < MIN_JD_LENGTH ? `${MIN_JD_LENGTH - len} more characters needed` : ''}</span>
        <span>{len.toLocaleString()} / {MAX_JD_LENGTH.toLocaleString()}</span>
      </div>
    </Field>
  );
}
