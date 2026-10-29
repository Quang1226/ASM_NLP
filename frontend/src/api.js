const BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data.detail === 'string'
      ? data.detail
      : Array.isArray(data.detail) && data.detail[0]?.msg
        ? data.detail[0].msg.replace(/^Value error,\s*/i, '')
        : 'The demo service is unavailable.';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

const json = (value) => JSON.stringify(value);

export const chatAPI = {
  health: () => request('/health'),
  start: () => request('/chat/start', { method: 'POST' }),
  message: (sessionId, text) => request('/chat/message', {
    method: 'POST', body: json({ session_id: sessionId, message_text: text }),
  }),
  contact: (payload) => request('/chat/contact', { method: 'POST', body: json(payload) }),
};

export const adminAPI = {
  login: (username, password) => request('/admin/login', {
    method: 'POST', body: json({ username, password }),
  }),
  call: (path, token, options = {}) => request(`/admin${path}`, {
    ...options, headers: { Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  }),
};
