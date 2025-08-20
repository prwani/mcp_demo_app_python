const log = document.getElementById('log');
const sendBtn = document.getElementById('send');
const msgEl = document.getElementById('msg');
const empEl = document.getElementById('employeeId');
const capsBtn = document.getElementById('show-capabilities');
const capsEl = document.getElementById('capabilities');

function saveConfig() {
  const cfg = getAoaiConfig();
  if (cfg) localStorage.setItem('aoai', JSON.stringify(cfg));
}

function loadConfig() {
  try {
    const raw = localStorage.getItem('aoai');
    if (!raw) return;
    const cfg = JSON.parse(raw);
    if (cfg.endpoint) document.getElementById('aoai-endpoint').value = cfg.endpoint;
    if (cfg.key) document.getElementById('aoai-key').value = cfg.key;
    if (cfg.api_version) document.getElementById('aoai-version').value = cfg.api_version;
    if (cfg.deployment) document.getElementById('aoai-deployment').value = cfg.deployment;
  } catch {}
}

function getAoaiConfig() {
  const endpoint = document.getElementById('aoai-endpoint').value.trim();
  const key = document.getElementById('aoai-key').value.trim();
  const api_version = document.getElementById('aoai-version').value.trim();
  const deployment = document.getElementById('aoai-deployment').value.trim();
  const cfg = {};
  if (endpoint) cfg.endpoint = endpoint;
  if (key) cfg.key = key;
  if (api_version) cfg.api_version = api_version;
  if (deployment) cfg.deployment = deployment;
  return Object.keys(cfg).length ? cfg : null;
}

function bubble(type, title, payload) {
  const div = document.createElement('div');
  div.className = `bubble ${type}`;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = title;
  div.appendChild(meta);
  if (typeof payload === 'string') {
    const p = document.createElement('div');
    p.textContent = payload;
    div.appendChild(p);
  } else {
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(payload, null, 2);
    div.appendChild(pre);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function chat() {
  const text = msgEl.value.trim();
  if (!text) return;
  const employee_id = empEl.value ? parseInt(empEl.value, 10) : null;
  const aoai = getAoaiConfig();

  bubble('user', 'You', text);
  msgEl.value = '';
  sendBtn.classList.add('loading');
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, employee_id, aoai })
    });
    const data = await res.json();
    const mode = data.routing_mode ? `mode=${data.routing_mode}` : 'mode=heuristic';
    bubble('bot', `Result (${mode})`, data);
  } catch (e) {
    bubble('bot', 'Error', e.message || String(e));
  } finally {
    sendBtn.classList.remove('loading');
  }
}

function attachExamples() {
  document.querySelectorAll('.chip[data-example]')?.forEach(chip => {
    chip.addEventListener('click', () => {
      msgEl.value = chip.getAttribute('data-example');
      msgEl.focus();
    });
  });
}

async function showCapabilities() {
  try {
    capsBtn.disabled = true;
    const res = await fetch('/mcp/capabilities');
    const data = await res.json();
    capsEl.classList.remove('hidden');
    capsEl.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  } catch (e) {
    capsEl.classList.remove('hidden');
    capsEl.innerHTML = `<div class="error">${e.message || String(e)}</div>`;
  } finally {
    capsBtn.disabled = false;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  loadConfig();
  attachExamples();
  // persist on input changes
  ['aoai-endpoint','aoai-key','aoai-version','aoai-deployment'].forEach(id => {
    const el = document.getElementById(id);
    el?.addEventListener('change', saveConfig);
    el?.addEventListener('blur', saveConfig);
  });

  sendBtn.addEventListener('click', chat);
  msgEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) chat();
  });
  capsBtn.addEventListener('click', showCapabilities);
});
