/**
 * src/api/client.js
 * Centralized API client. All requests go through /api (proxied to :8000).
 */

const BASE = '/api';

async function request(method, path, { params, body, file } = {}) {
  let url = BASE + path;

  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += '?' + qs;
  }

  const opts = { method };

  if (file) {
    const fd = new FormData();
    fd.append('file', file);
    opts.body = fd;
  } else if (body) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(url, opts);

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  return res.json();
}

// ── Endpoints ─────────────────────────────────────────

/** POST /upload — upload a file for indexing */
export const uploadFile = (file) =>
  request('POST', '/upload', { file });

/** POST /github — clone + index a GitHub repo */
export const ingestGithub = (repo_url) =>
  request('POST', '/github', { params: { repo_url } });

/** POST /chat — send a query, get answer + sources */
export const sendChat = (query) =>
  request('POST', '/chat', { params: { query } });

/** POST /search — semantic search, returns ranked results */
export const searchCode = (query) =>
  request('POST', '/search', { params: { query } });

/** GET /stats — system stats + indexed documents */
export const getStats = () =>
  request('GET', '/stats');

/** GET /settings — get system settings with masked keys */
export const getSettings = () =>
  request('GET', '/settings');

/** POST /settings — update runtime & persistent settings */
export const updateSettings = (settingsData) =>
  request('POST', '/settings', { body: settingsData });

/** POST /settings/test-key — test API key connectivity */
export const testApiKey = ({ provider, api_key, model }) =>
  request('POST', '/settings/test-key', { body: { provider, api_key, model } });

/** POST /settings/clear-index — clear all indexed vectors and tokens */
export const clearKnowledgeBase = () =>
  request('POST', '/settings/clear-index');
