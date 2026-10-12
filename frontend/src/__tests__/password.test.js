import { describe, expect, it } from 'vitest';
import { checkPassword, isPasswordValid, isValidEmail } from '../utils/password';

describe('password rules (mirror of backend policy)', () => {
  it('accepts a password meeting every rule', () => {
    expect(isPasswordValid('Str0ng!Passw0rd')).toBe(true);
  });

  it.each([
    ['Sh0rt!', 'length'],
    ['alllower1!', 'upper'],
    ['ALLUPPER1!', 'lower'],
    ['NoNumbers!!', 'number'],
    ['NoSpecial123', 'special'],
  ])('rejects %s (fails %s)', (password, ruleId) => {
    expect(isPasswordValid(password)).toBe(false);
    const failed = checkPassword(password).filter((r) => !r.met).map((r) => r.id);
    expect(failed).toContain(ruleId);
  });

  it('rejects passwords over the max length', () => {
    expect(isPasswordValid(`Aa1!${'x'.repeat(130)}`)).toBe(false);
  });
});

describe('email validation', () => {
  it.each(['jane@example.com', ' jane.doe+jobs@mail.co.in '])('accepts %s', (email) => {
    expect(isValidEmail(email)).toBe(true);
  });
  it.each(['', 'jane', 'jane@', 'jane@example', 'a b@example.com'])('rejects %s', (email) => {
    expect(isValidEmail(email)).toBe(false);
  });
});
