// Mirrors backend/app/auth/password_policy.py for instant feedback.
// The backend copy is the one that's enforced.
export const PASSWORD_RULES = [
  { id: 'length', label: 'At least 8 characters', test: (p) => p.length >= 8 },
  { id: 'upper', label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { id: 'lower', label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
  { id: 'number', label: 'One number', test: (p) => /\d/.test(p) },
  { id: 'special', label: 'One special character (e.g. ! @ # $)', test: (p) => /[^A-Za-z0-9]/.test(p) },
];

export const MAX_PASSWORD_LENGTH = 128;

export function checkPassword(password) {
  return PASSWORD_RULES.map((rule) => ({ ...rule, met: rule.test(password) }));
}

export function isPasswordValid(password) {
  return password.length <= MAX_PASSWORD_LENGTH && PASSWORD_RULES.every((rule) => rule.test(password));
}

export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());
}
