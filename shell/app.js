// Aether shell — P2: voice path, computer-use execute, Priority, Make it real, IPC

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

let currentPlanBookmark = null;
let runtimeOnline = false;
let currentVoiceSession = null;

let localPriority = [
  { id: 'p1', title: 'Connect live Grok Voice Think Fast 2.0 key and run first real session', meta: 'High impact · Now', level: 'high' },
  { id: 'p2', title: 'Exercise computer-use confirmation once with real screenshot', meta: 'Safety · Today', level: 'high' },
];

let localBookmarks = [
  {
    id: 'b1', category: 'Immediate', title: 'Grok Voice Think Fast 2.0 — go live with Realtime path',
    source: 'x.ai', score: 9.5,
    plan: ['Set GROK_VOICE_API_KEY', 'Start session via /voice/start', 'Drive presence states', 'Confirm text fallback']
  },
  {
    id: 'b2', category: 'Act soon', title: 'Computer-use real surfaces behind spoken gates',
    source: 'Aether', score: 8.9,
    plan: ['Shell exposes screenshot', 'Runtime requests → spoken confirm → shell executes', 'Audit every step']
  },
  {
    id: 'b3', category: 'Possibility', title: 'Content ideation + smart engagement tools',
    source: 'Aether', score: 8.3,
    plan: ['Use /content/ideate', 'Use /content/replies', 'Surface audience insight on first-use']
  }
];

function applyPresence(state) {
  if (!state) return;
  const { expression = 'neutral', status = 'idle', intensity = 0.5 } = state;
  presenceOrb.className = 'presence-orb ' + status;
  presenceStatus.textContent = status;
  presenceExpression.textContent = expression + ' · ' + Math.round(intensity * 100) + '%';
  if (window.aetherAPI) window.aetherAPI.setPresence(state);
}

async function api(path, options = {}) {
  try {
    const res = await fetch(RUNTIME_URL + path, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.json();
  } catch (e) {
    return null;
  }
}

async function checkRuntime() {
  const health = await api('/health');
  runtimeOnline = !!(health && health.status === 'ok');
  runtimeDot.className = 'dot ' + (runtimeOnline ? 'ok' : 'warn');
  let label = runtimeOnline ? 'Runtime: connected (:7420)' : 'Runtime: offline (local data)';
  if (health && health.voice_live) label += ' · voice live';
  runtimeLabel.textContent = label;
  return runtimeOnline;
}

function renderPriority(items) {
  const data = items || localPriority;
  priorityList.innerHTML = data.map(item => `
    <li class="priority-item" data-id="${item.id}">
      <div class="priority-icon ${item.level}">${item.level === 'high' ? '!' : '•'}</div>
      <div class="priority-content">
        <div class="priority-title">${item.title}</div>
        <div class="priority-meta">${item.meta || ''}</div>
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
        <ul class="plan-steps">${item.plan.map(s => `<li>${s}</li>`).join('')}</ul>
        <button class="make-real-btn" data-id="${item.id}">Make it real →</button>
      </div>` : '';
    return `
      <li class="bookmark-item" data-id="${item.id}">
        <div class="bookmark-top">
          <div class="score-badge ${cat}">${item.category}</div>
          <div class="bookmark-content">
            <div class="bookmark-title">${item.title}</div>
            <div class="bookmark-source">${item.source || ''}</div>
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

function openPlanModal(id) {
  const item = localBookmarks.find(b => b.id === id);
  if (!item || !item.plan) return;
  currentPlanBookmark = item;
  document.getElementById('planTitle').textContent = item.title;
  document.getElementById('planBody').innerHTML = `
    <p>This high-signal item already has a ready action plan:</p>
    <ol>${item.plan.map(s => `<li>${s}</li>`).join('')}</ol>
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
      applyPresence(result.presence || { expression: 'pleased', status: 'speaking', intensity: 0.7 });
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
    applyPresence({ expression: 'pleased', status: 'speaking', intensity: 0.7 });
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
  applyPresence({ expression: 'attentive', status: 'thinking', intensity: 0.6 });
  setTimeout(() => applyPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }), 1600);
}

async function runFirstUse() {
  applyPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.7 });
  sessionLabel.textContent = 'First-use…';
  let magic = runtimeOnline ? await api('/first-use') : null;
  if (!magic) {
    magic = {
      moves: [
        { title: 'Start a live voice session', why: 'Presence becomes real with voice' },
        { title: 'Run one computer-use confirmation', why: 'Prove spoken safety gate' },
        { title: 'Ideate a thread and promote best angle', why: 'Close signal → Priority loop' }
      ],
      presence: { expression: 'pleased', status: 'speaking', intensity: 0.8 }
    };
  }
  applyPresence(magic.presence || { expression: 'pleased', status: 'speaking', intensity: 0.8 });
  sessionLabel.textContent = 'First-use ready';
  if (magic.moves) {
    const moves = magic.moves.map((m, i) => ({
      id: 'fu-' + i, title: m.title, meta: m.why || 'Suggestion', level: 'high'
    }));
    renderPriority([...moves, ...localPriority].slice(0, 6));
  }
}

async function startSession() {
  applyPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 });
  sessionLabel.textContent = 'Starting voice session…';
  if (runtimeOnline) {
    const sess = await api('/voice/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: 'local', mode: 'reactive' })
    });
    if (sess && (sess.status === 'session_started' || sess.session_id)) {
      currentVoiceSession = sess.session_id;
      sessionLabel.textContent = sess.live ? 'Voice live' : 'Voice sim · ' + (sess.mode || 'reactive');
      applyPresence(sess.presence || { expression: 'attentive', status: 'listening', intensity: 0.8 });
      return;
    }
  }
  sessionLabel.textContent = 'Session: local stub';
}

/** P2: request screenshot via runtime confirmation then execute on shell */
async function demoComputerUse() {
  if (!runtimeOnline) {
    sessionLabel.textContent = 'Runtime offline — start aether --serve';
    return;
  }
  applyPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.6 });
  sessionLabel.textContent = 'Requesting screenshot…';
  const req = await api('/computer-use/request', {
    method: 'POST',
    body: JSON.stringify({ action: 'screenshot', details: { reason: 'panel demo' } })
  });
  if (!req || !req.request_id) {
    sessionLabel.textContent = 'Request failed';
    return;
  }
  sessionLabel.textContent = 'Awaiting confirmation…';
  // Auto-confirm for demo (in real voice flow this would be spoken)
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
      applyPresence({ expression: 'pleased', status: 'speaking', intensity: 0.75 });
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
document.getElementById('firstUseBtn').addEventListener('click', runFirstUse);
document.getElementById('startSessionBtn').addEventListener('click', startSession);
document.getElementById('closeModal').addEventListener('click', closePlanModal);
document.getElementById('cancelPlan').addEventListener('click', closePlanModal);
document.getElementById('confirmMakeReal').addEventListener('click', confirmMakeReal);

// Double-click presence orb = computer-use demo
presenceOrb.addEventListener('dblclick', demoComputerUse);

if (window.aetherAPI) {
  window.aetherAPI.onPresenceUpdate((_e, state) => applyPresence(state));
  window.aetherAPI.onFocusCapture(() => { captureInput.focus(); captureInput.select(); });
  window.aetherAPI.getPresence().then(applyPresence);
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
