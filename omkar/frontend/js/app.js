const BASE_URL = 'http://localhost:5001/api';

async function api(endpoint, method = 'GET', body = null) {
  const token = localStorage.getItem('token');
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(token ? { 'Authorization': 'Bearer ' + token } : {})
    }
  };
  if (body) opts.body = JSON.stringify(body);

  try {
    const res = await fetch(BASE_URL + endpoint, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Something went wrong');
    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Cannot connect to server. Make sure Python backend is running (python server.py)');
    }
    throw err;
  }
}

const val = id => document.getElementById(id)?.value?.trim() || '';

function showAlert(msg, type = 'error') {
  const el = document.getElementById('alert');
  if (!el) return;
  el.textContent = msg;
  el.className = 'alert alert-' + type + ' show';
  setTimeout(() => el.classList.remove('show'), 5000);
}

function showAlertIn(id, msg, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = 'alert alert-' + type + ' show';
  setTimeout(() => el.classList.remove('show'), 5000);
}

function hideAlert() {
  const el = document.getElementById('alert');
  if (el) el.classList.remove('show');
}

function getUser() {
  try { return JSON.parse(localStorage.getItem('user')) || {}; } catch { return {}; }
}

function requireAuth(role) {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');
  if (!token || userRole !== role) {
    window.location.href = role === 'donor' ? 'donor-login.html' : 'hospital-login.html';
  }
}

function logout() {
  localStorage.clear();
  window.location.href = 'index.html';
}
