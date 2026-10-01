const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function getToken() {
  return localStorage.getItem('token');
}

export function setToken(token) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
}

async function request(path, { method = 'GET', body, isForm = false, auth = true } = {}) {
  const headers = {};
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let payload = body;
  if (body && !isForm) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // response wasn't JSON, keep default detail
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

// --- Auth ---
export const register = (email, password) =>
  request('/auth/register', { method: 'POST', body: { email, password }, auth: false });

export const login = async (email, password) => {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Login failed');
  }
  return res.json();
};

// --- Resume ---
export const uploadResume = (file) => {
  const form = new FormData();
  form.append('file', file);
  return request('/resume/upload', { method: 'POST', body: form, isForm: true });
};

export const getMyResume = () => request('/resume/me');

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
