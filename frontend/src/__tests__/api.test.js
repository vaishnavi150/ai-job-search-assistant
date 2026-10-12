import { afterEach, describe, expect, it, vi } from 'vitest';
import * as api from '../api';

const store = {};
vi.stubGlobal('localStorage', {
  getItem: (k) => store[k] ?? null,
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
});

function mockFetch(status, body) {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.stubGlobal('localStorage', {
    getItem: (k) => store[k] ?? null,
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
  });
});

describe('errorMessageFrom', () => {
  it('prefers the server detail string', () => {
    expect(api.errorMessageFrom(400, { detail: 'Upload a resume first.' })).toBe('Upload a resume first.');
  });
  it('joins pydantic-style detail lists', () => {
    expect(api.errorMessageFrom(422, { detail: [{ msg: 'a' }, { msg: 'b' }] })).toBe('a b');
  });
  it('has friendly fallbacks', () => {
    expect(api.errorMessageFrom(429, null)).toMatch(/Too many/);
    expect(api.errorMessageFrom(502, null)).toMatch(/server/);
  });
});

describe('request handling', () => {
  it('sends the bearer token and parses JSON', async () => {
    api.setToken('abc');
    mockFetch(200, { email: 'jane@example.com' });
    await expect(api.getMe()).resolves.toEqual({ email: 'jane@example.com' });
    const [, init] = fetch.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer abc');
  });

  it('emits api:unauthorized on 401 for authenticated calls', async () => {
    const handler = vi.fn();
    const off = api.onApiEvent('api:unauthorized', handler);
    mockFetch(401, { detail: 'Your session has expired. Please log in again.' });
    await expect(api.getMe()).rejects.toMatchObject({ status: 401 });
    expect(handler).toHaveBeenCalledOnce();
    off();
  });

  it('does not treat a failed login as an expired session', async () => {
    const handler = vi.fn();
    const off = api.onApiEvent('api:unauthorized', handler);
    mockFetch(401, { detail: 'Incorrect email or password.' });
    await expect(api.login('a@b.co', 'x')).rejects.toThrow('Incorrect email or password.');
    expect(handler).not.toHaveBeenCalled();
    off();
  });

  it('reports network failures clearly', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch'); }));
    await expect(api.listApplications()).rejects.toThrow(/Can't reach the server/);
  });

  it('never puts the reset token in the URL of API calls', async () => {
    mockFetch(200, { message: 'ok' });
    await api.resetPassword('secret-token-value', 'Str0ng!Pass', 'Str0ng!Pass');
    const [url, init] = fetch.mock.calls[0];
    expect(url).not.toContain('secret-token-value');
    expect(JSON.parse(init.body).token).toBe('secret-token-value');
  });
});
