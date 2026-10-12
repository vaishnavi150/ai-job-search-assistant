const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

const TOKEN_KEY = 'token';
const SLOW_REQUEST_MS = 4000;
const DEFAULT_TIMEOUT_MS = 90_000;

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // storage blocked (private mode) - session lasts until the tab closes
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('email'); // legacy key from v0.1
  } catch {
    // ignore
  }
}

// --- Cross-cutting events the UI listens to ---
// `api:unauthorized` -> session expired, AuthContext logs out.
// `api:slow` / `api:settled` -> show "waking up the server" on cold starts.
const events = new EventTarget();
export const onApiEvent = (type, handler) => {
  events.addEventListener(type, handler);
  return () => events.removeEventListener(type, handler);
};

let pending = 0;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function errorMessageFrom(status, data) {
  const detail = data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg || String(d)).join(' ');
  if (status === 429) return 'Too many requests. Please wait a moment and try again.';
  if (status >= 500) return 'The server ran into a problem. Please try again.';
  return `Request failed (${status}).`;
}

async function request(path, { method = 'GET', body, form, auth = true, timeout = DEFAULT_TIMEOUT_MS } = {}) {
  const headers = {};
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let payload;
  if (form instanceof FormData) {
    payload = form;
  } else if (form instanceof URLSearchParams) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
    payload = form;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const slowTimer = setTimeout(() => events.dispatchEvent(new Event('api:slow')), SLOW_REQUEST_MS);
  pending += 1;

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload, signal: controller.signal });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new ApiError('The request timed out. The server may be busy - please try again.', 0);
    }
    throw new ApiError("Can't reach the server. Check your connection and try again.", 0);
  } finally {
    clearTimeout(timer);
    clearTimeout(slowTimer);
    pending -= 1;
    if (pending === 0) events.dispatchEvent(new Event('api:settled'));
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    if (res.status === 401 && auth) {
      events.dispatchEvent(new Event('api:unauthorized'));
    }
    throw new ApiError(errorMessageFrom(res.status, data), res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

// --- Auth ---
export const register = (email, password, confirmPassword) =>
  request('/auth/register', {
    method: 'POST',
    body: { email, password, confirm_password: confirmPassword },
    auth: false,
  });

export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  return request('/auth/login', { method: 'POST', form, auth: false });
};

export const getMe = () => request('/auth/me');
export const logoutAll = () => request('/auth/logout-all', { method: 'POST' });

export const changePassword = (currentPassword, newPassword, confirmPassword) =>
  request('/auth/change-password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword, confirm_password: confirmPassword },
  });

export const forgotPassword = (email) =>
  request('/auth/forgot-password', { method: 'POST', body: { email }, auth: false });

export const validateResetToken = (token) =>
  request('/auth/reset-password/validate', { method: 'POST', body: { token }, auth: false });

export const resetPassword = (token, password, confirmPassword) =>
  request('/auth/reset-password', {
    method: 'POST',
    body: { token, password, confirm_password: confirmPassword },
    auth: false,
  });

export const getServerConfig = () => request('/config', { auth: false });

// --- Resume ---
export const uploadResume = (file) => {
  const form = new FormData();
  form.append('file', file);
  return request('/resume/upload', { method: 'POST', form });
};

export const getMyResume = () => request('/resume/me');
export const deleteMyResume = () => request('/resume/me', { method: 'DELETE' });

// --- Jobs ---
export const searchJobs = ({ q, location = '', remoteOnly = false, limit = 20 }) => {
  const params = new URLSearchParams({ q, location, remote_only: String(remoteOnly), limit: String(limit) });
  return request(`/jobs/search?${params}`);
};

// --- Matching ---
export const matchResume = (jobDescription) =>
  request('/match', { method: 'POST', body: { job_description: jobDescription } });

export const tailorBullets = (jobDescription) =>
  request('/match/bullets', { method: 'POST', body: { job_description: jobDescription } });

// --- Interview ---
export const getInterviewQuestions = (jobDescription, numQuestions = 5) =>
  request('/interview/questions', {
    method: 'POST',
    body: { job_description: jobDescription, num_questions: numQuestions },
  });

export const mockInterviewReply = (jobDescription, history) =>
  request('/interview/mock', { method: 'POST', body: { job_description: jobDescription, history } });

// --- Applications ---
export const listApplications = () => request('/applications');

export const createApplication = (payload) =>
  request('/applications', { method: 'POST', body: payload });

export const updateApplication = (id, payload) =>
  request(`/applications/${id}`, { method: 'PATCH', body: payload });

export const deleteApplication = (id) =>
  request(`/applications/${id}`, { method: 'DELETE' });

// --- Chat assistant ---
export const sendChatMessage = (message) =>
  request('/chat', { method: 'POST', body: { message } });
