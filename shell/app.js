// Aether shell — presence loop fixed, First-use + Start Session hardened

const RUNTIME_URL = 'http://127.0.0.1:7420';

const presenceOrb = document.getElementById('presenceOrb');
const presenceStatus = document.getElementById('presenceStatus');
const presenceExpression = document.getElementById('presenceExpression');
const captureInput = document.getElementById('captureInput');
const runtimeLabel = document.getElementById('runtimeLabel');
const runtimeDot = document.getElementById('runtimeDot');
const sessionLabel = document.getElementById('sessionLabel');
const priorityList = document.getElementById('priorityList');
const bookmarkList = document.getElementById('bookmarkList');
const firstUseBtn = document.getElementById('firstUseBtn');
const startSessionBtn = document.getElementById('startSessionBtn');

let currentPlanBookmark = null;
let runtimeOnline = false;
let currentVoiceSession = null;
let lastPresenceKey = '';
let presenceSettleTimer = null;
let busy = false;

let localPriority = [
  { id: 'p1', title: 'Connect live Grok Voice key and run first real session', meta: 'High impact · Now', level: 'high' },
  { id: 'p2', title: 'Exercise computer-use confirmation once', meta: 'Safety · Today', level: 'high' },
];

let localBookmarks = [
  {
    id: 'b1', category: 'Immediate', title: 'Grok Voice Think Fast 2.0 — go live',
    source: 'x.ai', score: 9.5,
    plan: ['Set GROK_VOICE_API_KEY', 'Start session', 'Drive presence states']
  },
  {
    id: 'b2', category: 'Act soon', title: 'Computer-use real surfaces behind spoken gates',
    source: 'Aether', score: 8.9,
    plan: ['Double-click orb for screenshot demo', 'Runtime confirm → shell execute']
  },
];

/** DOM-only presence update. Never push to main from here. */
function renderPresence(state) {
  if (!state) return;
  const expression = state.expression || 'neutral';
  const status = state.status || 'idle';
  const intensity = typeof state.intensity === 'number' ? state.intensity : 0.5;
  const key = expression + '|' + status + '|' + Math.round(intensity * 100);
  if (key === lastPresenceKey) return;
  lastPresenceKey = key;
  presenceOrb.className = 'presence-orb ' + status;
  presenceStatus.textContent = status;
  presenceExpression.textContent = expression + ' · ' + Math.round(intensity * 100) + '%';
}

/** Intentional presence change from UI actions — update DOM + notify main once. */
function setPresence(state, settleMs = 0) {
  renderPresence(state);
  if (window.aetherAPI) {
    try { window.aetherAPI.setPresence(state); } catch (_) {}
  }
  if (presenceSettleTimer) clearTimeout(presenceSettleTimer);
  if (settleMs > 0) {
    presenceSettleTimer = setTimeout(() => {
      setPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }, 0);
    }, settleMs);
  }
}

async function api(path, options = {}) {
  try {
    const res = await fetch(RUNTIME_URL + path, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error('HTTP ' + res.status + (text ? ': ' + text.slice(0, 120) : ''));
    }
    return await res.json();
  } catch (e) {
    console.warn('API', path, e);
    return null;
  }
}

async function checkRuntime() {
  const health = await api('/health');
  runtimeOnline = !!(health && health.status === 'ok');
  runtimeDot.className = 'dot ' + (runtimeOnline ? 'ok' : 'warn');
  let label = runtimeOnline ? 'Runtime: connected (:7420)' : 'Runtime: offline (local data)';
  if (health && health.voice_live) label += ' · voice live';
  if (health && health.memory && health.memory.backend) label += ' · ' + health.memory.backend;
  runtimeLabel.textContent = label;
  return runtimeOnline;
}

function renderPriority(items) {
  const data = items || localPriority;
  priorityList.innerHTML = data.map(item => `
    <li class="priority-item" data-id="${item.id}">
      <div class="priority-icon ${item.level}">${item.level === 'high' ? '!' : '•'}</div>
      <div class="priority-content">
        <div class="priority-title">${escapeHtml(item.title)}</div>
        <div class="priority-meta">${escapeHtml(item.meta || '')}</div>
      </div>
      <div class="priority-tag ${item.level}">${item.level}</div>
    </li>
  `).join('');
}

function renderBookmarks(items) {
  const data = items || localBookmarks;
  bookmarkList.innerHTML = data.map(item => {
    const cat = (item.category || '').toLowerCase().replace(/\s+/g, '');
    const planHtml = item.plan && item.plan.length ? `
      <div class="action-plan">
        <div class="plan-label">Ready Action Plan</div>
        <ul class="plan-steps">${item.plan.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul>
        <button class="make-real-btn" data-id="${item.id}">Make it real →</button>
      </div>` : '';
    return `
      <li class="bookmark-item" data-id="${item.id}">
        <div class="bookmark-top">
          <div class="score-badge ${cat}">${escapeHtml(item.category || '')}</div>
          <div class="bookmark-content">
            <div class="bookmark-title">${escapeHtml(item.title)}</div>
            <div class="bookmark-source">${escapeHtml(item.source || '')}</div>
          </div>
          <div class="score-number">${item.score || ''}</div>
        </div>
        ${planHtml}
      </li>`;
  }).join('');

  document.querySelectorAll('.make-real-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openPlanModal(btn.dataset.id);
    });
  });
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function openPlanModal(id) {
  const item = localBookmarks.find(b => b.id === id);
  if (!item || !item.plan) return;
  currentPlanBookmark = item;
  document.getElementById('planTitle').textContent = item.title;
  document.getElementById('planBody').innerHTML = `
    <p>This high-signal item already has a ready action plan:</p>
    <ol>${item.plan.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ol>
    <p style="margin-top:10px;font-size:12px;color:var(--text-muted)">
      “Make it real” pushes it into Priority as high impact.
    </p>`;
  document.getElementById('planModal').classList.remove('hidden');
}

function closePlanModal() {
  document.getElementById('planModal').classList.add('hidden');
  currentPlanBookmark = null;
}

async function confirmMakeReal() {
  if (!currentPlanBookmark) return;
  const id = currentPlanBookmark.id;
  if (runtimeOnline) {
    const result = await api('/make-it-real', {
      method: 'POST',
      body: JSON.stringify({ bookmark_id: id })
    });
    if (result && result.status === 'promoted') {
      setPresence(result.presence || { expression: 'pleased', status: 'speaking', intensity: 0.7 }, 2200);
      sessionLabel.textContent = 'Promoted to Priority';
      const pri = await api('/priority');
      if (pri && pri.items) { localPriority = pri.items; renderPriority(pri.items); }
    }
  } else {
    localPriority.unshift({
      id: 'p-' + Date.now(),
      title: currentPlanBookmark.title,
      meta: 'From Bookmark · just now',
      level: 'high'
    });
    renderPriority();
    setPresence({ expression: 'pleased', status: 'speaking', intensity: 0.7 }, 2200);
    sessionLabel.textContent = 'Promoted (local)';
  }
  closePlanModal();
  switchView('priority');
}

function switchView(view) {
  document.getElementById('priorityView').classList.toggle('active', view === 'priority');
  document.getElementById('bookmarkView').classList.toggle('active', view === 'bookmarks');
}

async function addCapture() {
  const text = captureInput.value.trim();
  if (!text) return;
  captureInput.value = '';
  if (runtimeOnline) {
    await api('/priority/add', { method: 'POST', body: JSON.stringify({ title: text, level: 'high' }) });
    const pri = await api('/priority');
    if (pri && pri.items) { localPriority = pri.items; renderPriority(pri.items); }
  } else {
    localPriority.unshift({ id: 'p-' + Date.now(), title: text, meta: 'Just captured · Now', level: 'high' });
    renderPriority();
  }
  sessionLabel.textContent = 'Captured';
  setPresence({ expression: 'attentive', status: 'thinking', intensity: 0.6 }, 1600);
}

async function runFirstUse() {
  if (busy) return;
  busy = true;
  firstUseBtn.disabled = true;
  try {
    setPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.7 }, 0);
    sessionLabel.textContent = 'First-use…';
    await checkRuntime();
    let magic = runtimeOnline ? await api('/first-use') : null;
    if (!magic) {
      magic = {
        moves: [
          { title: 'Start a voice session', why: 'Presence becomes real with voice' },
          { title: 'Confirm Postgres + Ollama in health', why: 'Local stack check' },
          { title: 'Capture one next move', why: 'Close signal → Priority' }
        ],
        presence: { expression: 'pleased', status: 'speaking', intensity: 0.8 },
        message: 'Offline first-use (start aether --serve for live)'
      };
    }
    setPresence(magic.presence || { expression: 'pleased', status: 'speaking', intensity: 0.8 }, 2800);
    sessionLabel.textContent = magic.message ? String(magic.message).slice(0, 48) : 'First-use ready';
    if (magic.moves && magic.moves.length) {
      const moves = magic.moves.map((m, i) => ({
        id: 'fu-' + i,
        title: m.title,
        meta: m.why || 'Suggestion',
        level: 'high'
      }));
      renderPriority([...moves, ...localPriority].slice(0, 6));
    }
  } finally {
    busy = false;
    firstUseBtn.disabled = false;
  }
}

async function startSession() {
  if (busy) return;
  busy = true;
  startSessionBtn.disabled = true;
  try {
    setPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 }, 0);
    sessionLabel.textContent = 'Starting voice session…';
    await checkRuntime();
    if (!runtimeOnline) {
      sessionLabel.textContent = 'Runtime offline — run aether --serve';
      setPresence({ expression: 'concerned', status: 'idle', intensity: 0.5 }, 0);
      return;
    }
    const sess = await api('/voice/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: 'local', mode: 'reactive' })
    });
    if (sess && (sess.status === 'session_started' || sess.session_id)) {
      currentVoiceSession = sess.session_id;
      const mode = sess.live ? 'live' : 'sim';
      sessionLabel.textContent = 'Session ' + (sess.session_id || '').slice(0, 14) + ' · ' + mode;
      setPresence(sess.presence || { expression: 'attentive', status: 'listening', intensity: 0.8 }, 0);
      return;
    }
    sessionLabel.textContent = 'Session start failed — check runtime log';
    setPresence({ expression: 'concerned', status: 'idle', intensity: 0.5 }, 0);
  } finally {
    busy = false;
    startSessionBtn.disabled = false;
  }
}

async function demoComputerUse() {
  if (!runtimeOnline) {
    sessionLabel.textContent = 'Runtime offline — start aether --serve';
    return;
  }
  setPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.6 }, 0);
  sessionLabel.textContent = 'Requesting screenshot…';
  const req = await api('/computer-use/request', {
    method: 'POST',
    body: JSON.stringify({ action: 'screenshot', details: { reason: 'panel demo' } })
  });
  if (!req || !req.request_id) {
    sessionLabel.textContent = 'Request failed';
    return;
  }
  sessionLabel.textContent = 'Confirming…';
  const conf = await api('/computer-use/confirm', {
    method: 'POST',
    body: JSON.stringify({ request_id: req.request_id, spoken_yes: true })
  });
  if (conf && conf.execute_on_shell && window.aetherAPI) {
    const result = await window.aetherAPI.executeComputerUse({
      action: conf.action,
      details: conf.details
    });
    if (result && result.ok) {
      sessionLabel.textContent = 'Screenshot saved';
      setPresence({ expression: 'pleased', status: 'speaking', intensity: 0.75 }, 2200);
    } else {
      sessionLabel.textContent = 'Execute failed: ' + (result && result.error ? result.error : 'unknown');
    }
  } else {
    sessionLabel.textContent = conf ? conf.status : 'Confirm failed';
  }
}

// Wire
document.getElementById('captureBtn').addEventListener('click', addCapture);
captureInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') addCapture(); });
document.getElementById('closeBtn').addEventListener('click', () => window.close());
document.getElementById('minimizeBtn').addEventListener('click', () => window.close());
document.getElementById('switchToBookmarks').addEventListener('click', () => switchView('bookmarks'));
document.getElementById('backToPriority').addEventListener('click', () => switchView('priority'));
firstUseBtn.addEventListener('click', runFirstUse);
startSessionBtn.addEventListener('click', startSession);
document.getElementById('closeModal').addEventListener('click', closePlanModal);
document.getElementById('cancelPlan').addEventListener('click', closePlanModal);
document.getElementById('confirmMakeReal').addEventListener('click', confirmMakeReal);

presenceOrb.addEventListener('dblclick', demoComputerUse);

if (window.aetherAPI) {
  // Main → renderer only: never push back (breaks feedback loop)
  window.aetherAPI.onPresenceUpdate((_e, state) => renderPresence(state));
  window.aetherAPI.onFocusCapture(() => { captureInput.focus(); captureInput.select(); });
  window.aetherAPI.getPresence().then((s) => renderPresence(s));
}

document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'a') {
    e.preventDefault();
    captureInput.focus();
  }
  if (e.key === 'Escape') closePlanModal();
});

(async () => {
  await checkRuntime();
  if (runtimeOnline) {
    const pri = await api('/priority');
    const bms = await api('/bookmarks');
    if (pri && pri.items) localPriority = pri.items;
    if (bms && bms.items) localBookmarks = bms.items;
  }
  renderPriority();
  renderBookmarks();
  setInterval(checkRuntime, 8000);
})();
