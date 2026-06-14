// ═══════════════════════════════════════════════════════════════════
//  SHARED UTILITIES — ORIO
// ═══════════════════════════════════════════════════════════════════

const API = 'http://127.0.0.1:8000/api';

// ── Token refresh ──────────────────────────────────────────────────
async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;
  try {
    const res = await fetch(`${API}/auth/token/refresh/`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ refresh }),
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('access_token', data.access);
      return true;
    }
    return false;
  } catch { return false; }
}

// ── Authenticated fetch with auto-refresh ─────────────────────────
async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('access_token');
  options.headers = { ...options.headers, 'Authorization': 'Bearer ' + token };

  let res = await fetch(url, options);

  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) { window.location.href = 'login.html'; return null; }
    options.headers['Authorization'] = 'Bearer ' + localStorage.getItem('access_token');
    res = await fetch(url, options);
  }

  return res;
}

// ── Toast notification ─────────────────────────────────────────────
let _toastTmr;
function toast(msg, type = '') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast ' + type;
  t.classList.add('show');
  clearTimeout(_toastTmr);
  _toastTmr = setTimeout(() => t.classList.remove('show'), 3200);
}

// ── Nav user init ──────────────────────────────────────────────────
function initNav() {
  const token = localStorage.getItem('access_token');
  if (!token) { window.location.href = 'login.html'; return false; }

  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if (user) {
    const nameEl = document.getElementById('nav-name');
    const avEl   = document.getElementById('nav-av');
    if (nameEl) nameEl.textContent = user.first_name || user.email;
    if (avEl)   avEl.textContent   = (user.first_name || 'U')[0].toUpperCase();
  }
  return true;
}