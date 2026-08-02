// Aether shell — P1: Priority + Action Plans + Make it real + IPC client

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

// Fallback local data (used when runtime is offline)
let localPriority = [
  { id: 'p1', title: 'Wire live Grok Voice Think Fast 2.0 path', meta: 'High impact · This week', level: 'high' },
  { id: 'p2', title: 'Complete typed IPC bridge + first-use magic', meta: 'Architecture · Today', level: 'high' },
];

let localBookmarks = [
  {
    id: 'b1', category: 'Immediate', title: 'Grok Voice Think Fast 2.0 now live — integrate Realtime path',
    source: 'x.ai / xAI', score: 9.4,
    plan: [
      'Confirm API endpoint + auth for Think Fast 2.0',
      'Add voice session start + partial transcript handling',
      'Push presence updates over IPC',
      'Add graceful fallback when STT confidence < floor'
    ]
  },
  {
    id: 'b2', category: 'Act soon', title: 'Computer-use tools with spoken confirmation gates',
    source: 'Aether design', score: 8.7,
    plan: [
      'Expose screenshot / window list / type / click from shell',
      'Require spoken confirmation before mutating actions',
      'Log every request + confirmation',
      'Surface confirmation in panel + voice'
    ]
  },
  {
    id: 'b3', category: 'Possibility', title: 'First-use magic: analyze + 3 next moves',
    source: 'Aether design', score: 8.1,
    plan: [
      'Detect first-run / empty memory',
      'Offer 3 concrete next moves',
      'Push accepted move into Priority via Make it real'
    ]
  }
];

function applyPresence(state) {
  if (!state) return;
  const { expression = 'neutral', status = 'idle', intensity = 0.5 } = state;
  presenceOrb.className = 'presence-orb ' + status;
  presenceStatus.textContent = status;
  presenceExpression.textContent = expression + ' · ' + Math.round(intensity * 100) + '%';
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
  runtimeLabel.textContent = runtimeOnline ? 'Runtime: connected (:7420)' : 'Runtime: offline (local data)';
  return runtimeOnline;
}

function renderPriority(items) {
  const data = items || localPriority;
  priorityList.innerHTML = data.map(item => `
    <li class="priority-item" data-id="${item.id}">
      <div class="priority-icon ${item.level}">${item.level === 'high' ? '!' : item.level === 'medium' ? '•' : '·'}</div>
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
  const items = localBookmarks;
  const item = items.find(b => b.id === id);
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
      if (pri && pri.items) {
        localPriority = pri.items;
        renderPriority(pri.items);
      }
    }
  } else {
    // Local fallback
    const newItem = {
      id: 'p-' + Date.now(),
      title: currentPlanBookmark.title,
      meta: 'From Bookmark · just now',
      level: 'high'
    };
    localPriority.unshift(newItem);
    renderPriority();
    applyPresence({ expression: 'pleased', status: 'speaking', intensity: 0.7 });
    sessionLabel.textContent = 'Promoted to Priority (local)';
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
    await api('/priority/add', {
      method: 'POST',
      body: JSON.stringify({ title: text, level: 'high' })
    });
    const pri = await api('/priority');
    if (pri && pri.items) {
      localPriority = pri.items;
      renderPriority(pri.items);
    }
  } else {
    localPriority.unshift({
      id: 'p-' + Date.now(),
      title: text,
      meta: 'Just captured · Now',
      level: 'high'
    });
    renderPriority();
  }
  sessionLabel.textContent = 'Captured · just now';
  applyPresence({ expression: 'attentive', status: 'thinking', intensity: 0.6 });
  setTimeout(() => applyPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }), 1800);
}

async function runFirstUse() {
  applyPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.7 });
  sessionLabel.textContent = 'First-use magic…';

  let magic = null;
  if (runtimeOnline) {
    magic = await api('/first-use');
  }

  if (!magic) {
    magic = {
      message: 'Welcome. Here are 3 concrete next moves for Aether.',
      moves: [
        { title: 'Connect live Grok Voice Think Fast 2.0', why: 'Unlock real-time voice presence' },
        { title: 'Run computer-use confirmation flow once', why: 'Verify spoken safety gates' },
        { title: 'Promote one high-score bookmark into Priority', why: 'Exercise Make it real loop' }
      ],
      presence: { expression: 'pleased', status: 'speaking', intensity: 0.8 }
    };
  }

  applyPresence(magic.presence || { expression: 'pleased', status: 'speaking', intensity: 0.8 });
  sessionLabel.textContent = 'First-use ready';

  // Surface moves as temporary priority items if empty-ish
  if (magic.moves && magic.moves.length) {
    const movesAsPriority = magic.moves.map((m, i) => ({
      id: 'fu-' + i,
      title: m.title,
      meta: m.why || 'First-use suggestion',
      level: 'high'
    }));
    // Show on top without permanently overwriting if runtime is live
    renderPriority([...movesAsPriority, ...localPriority].slice(0, 6));
  }
}

async function startSession() {
  applyPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 });
  sessionLabel.textContent = 'Session starting…';

  if (runtimeOnline) {
    const sess = await api('/session/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: 'local', mode: 'reactive' })
    });
    if (sess && sess.status === 'session_started') {
      sessionLabel.textContent = 'Session: ' + (sess.mode || 'reactive');
      applyPresence({ expression: 'attentive', status: 'listening', intensity: 0.8 });
      return;
    }
  }

  sessionLabel.textContent = 'Session: local stub';
}

// Wire events
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

// Boot
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
  // Re-check every 8s
  setInterval(checkRuntime, 8000);
})();
