import { describe, expect, it } from 'vitest';
import { clearOnEdit } from '../utils/forms';

// Minimal stand-in for React's useState setters.
function state(initial) {
  const box = { value: initial };
  box.set = (next) => { box.value = typeof next === 'function' ? next(box.value) : next; };
  return box;
}

describe('clearOnEdit', () => {
  it('sets the value and clears the listed field errors', () => {
    const value = state('');
    const errors = state({ password: 'Too weak', confirm: 'Passwords don’t match.', email: 'Bad email' });
    clearOnEdit(value.set, errors.set, 'password', 'confirm')('N3w!Password9');
    expect(value.value).toBe('N3w!Password9');
    expect(errors.value).toEqual({ password: '', confirm: '', email: 'Bad email' });
  });

  it('leaves the errors object untouched when there is nothing to clear', () => {
    const value = state('');
    const original = { email: 'Bad email' };
    const errors = state(original);
    clearOnEdit(value.set, errors.set, 'password')('x');
    expect(errors.value).toBe(original);
  });
});
