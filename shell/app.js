// Aether shell — talk loop + auto runtime + priority levels

const RUNTIME_URL = 'http://127.0.0.1:7420';

const presenceOrb = document.getElementById('presenceOrb');
const presenceStatus = document.getElementById('presenceStatus');
const presenceExpression = document.getElementById('presenceExpression');
const captureInput = document.getElementById('captureInput');
const captureLabel = document.getElementById('captureLabel');
const captureHint = document.getElementById('captureHint');
const runtimeLabel = document.getElementById('runtimeLabel');
const runtimeDot = document.getElementById('runtimeDot');
const sessionLabel = document.getElementById('sessionLabel');
const priorityList = document.getElementById('priorityList');
const bookmarkList = document.getElementById('bookmarkList');
const firstUseBtn = document.getElementById('firstUseBtn');
const startSessionBtn = document.getElementById('startSessionBtn');
const talkLog = document.getElementById('talkLog');
const talkMessages = document.getElementById('talkMessages');

let currentPlanBookmark = null;
let runtimeOnline = false;
let currentVoiceSession = null;
let lastPresenceKey = '';
let presenceSettleTimer = null;
let busy = false;

let localPriority = [
  { id: 'p1', title: 'Type a message after Start Session', meta: 'Talk · Now', level: 'medium' },
  { id: 'p2', title: 'Set GROK_VOICE_API_KEY for live voice later', meta: 'Optional', level: 'low' },
];

let localBookmarks = [
  {
    id: 'b1', category: 'Immediate', title: 'Talk in-session (text path now, voice later)',
    source: 'Aether', score: 9.2,
    plan: ['Start Session', 'Type in the box', 'Read agent reply in SESSION']
  },
];

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

function setPresence(state, settleMs = 0) {
  renderPresence(state);
  if (window.aetherAPI) {
    try { window.aetherAPI.setPresence(state); } catch (_) {}
  }
  if (presenceSettleTimer) clearTimeout(presenceSettleTimer);
  if (settleMs > 0) {
    presenceSettleTimer = setTimeout(() => {
      // Keep listening if session still active
      if (currentVoiceSession) {
        setPresence({ expression: 'attentive', status: 'listening', intensity: 0.7 }, 0);
      } else {
        setPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }, 0);
      }
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
  let label = runtimeOnline ? 'Runtime: connected (:7420)' : 'Runtime: offline';
  if (health && health.memory && health.memory.backend) label += ' · ' + health.memory.backend;
  if (health && health.voice_live) label += ' · voice live';
  runtimeLabel.textContent = label;
  return runtimeOnline;
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderPriority(items) {
  const data = items || localPriority;
  priorityList.innerHTML = data.map(item => {
    const level = item.level || 'medium';
    return `
    <li class="priority-item" data-id="${item.id}">
      <div class="priority-icon ${level}">${level === 'high' ? '!' : (level === 'low' ? '✓' : '•')}</div>
      <div class="priority-content">
        <div class="priority-title">${escapeHtml(item.title)}</div>
        <div class="priority-meta">${escapeHtml(item.meta || '')}</div>
      </div>
      <div class="priority-tag ${level}">${level}</div>
    </li>`;
  }).join('');
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

function openPlanModal(id) {
  const item = localBookmarks.find(b => b.id === id);
  if (!item || !item.plan) return;
  currentPlanBookmark = item;
  document.getElementById('planTitle').textContent = item.title;
  document.getElementById('planBody').innerHTML = `
    <p>Ready action plan:</p>
    <ol>${item.plan.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ol>`;
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
      setPresence(result.presence || { expression: 'pleased', status: 'speaking', intensity: 0.7 }, 1800);
      sessionLabel.textContent = 'Promoted to Priority';
      const pri = await api('/priority');
      if (pri && pri.items) { localPriority = pri.items; renderPriority(pri.items); }
    }
  } else {
    localPriority.unshift({
      id: 'p-' + Date.now(),
      title: currentPlanBookmark.title,
      meta: 'From Bookmark · just now',
      level: 'medium'
    });
    renderPriority();
  }
  closePlanModal();
  switchView('priority');
}

function switchView(view) {
  document.getElementById('priorityView').classList.toggle('active', view === 'priority');
  document.getElementById('bookmarkView').classList.toggle('active', view === 'bookmarks');
}

function setTalkMode(on) {
  if (on) {
    talkLog.classList.remove('hidden');
    captureLabel.textContent = 'TALK TO AETHER';
    captureInput.placeholder = 'Say something… (Enter to send)';
    captureHint.textContent = 'Session active · Enter sends a turn · Start Session again ends it';
    startSessionBtn.textContent = 'End Session';
  } else {
    talkLog.classList.add('hidden');
    talkMessages.innerHTML = '';
    captureLabel.textContent = 'QUICK CAPTURE';
    captureInput.placeholder = 'Capture a thought or next move…';
    captureHint.textContent = 'Ctrl + Alt + A · or type and press Enter';
    startSessionBtn.textContent = 'Start Session';
  }
}

function appendTalk(role, text) {
  const div = document.createElement('div');
  div.className = 'talk-bubble ' + role;
  div.textContent = text;
  talkMessages.appendChild(div);
  talkMessages.scrollTop = talkMessages.scrollHeight;
}

async function sendTurn(text) {
  if (!currentVoiceSession || !text) return;
  appendTalk('user', text);
  setPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.65 }, 0);
  sessionLabel.textContent = 'Thinking…';
  const result = await api('/voice/turn', {
    method: 'POST',
    body: JSON.stringify({ session_id: currentVoiceSession, transcript: text })
  });
  if (!result || result.error) {
    appendTalk('agent', result && result.error ? result.error : 'No response (is runtime up?)');
    setPresence({ expression: 'concerned', status: 'listening', intensity: 0.6 }, 0);
    sessionLabel.textContent = 'Turn failed';
    return;
  }
  const reply = result.response || result.message || JSON.stringify(result).slice(0, 200);
  appendTalk('agent', reply);
  setPresence(result.presence || { expression: 'attentive', status: 'speaking', intensity: 0.8 }, 2200);
  sessionLabel.textContent = 'Turn ' + (result.turn || '') + (result.live ? ' · live' : ' · sim');
}

async function onCaptureOrTalk() {
  const text = captureInput.value.trim();
  if (!text) return;
  captureInput.value = '';
  if (currentVoiceSession) {
    await sendTurn(text);
    return;
  }
  // Priority capture
  if (runtimeOnline) {
    await api('/priority/add', { method: 'POST', body: JSON.stringify({ title: text, level: 'medium' }) });
    const pri = await api('/priority');
    if (pri && pri.items) { localPriority = pri.items; renderPriority(pri.items); }
  } else {
    localPriority.unshift({ id: 'p-' + Date.now(), title: text, meta: 'Just captured · Now', level: 'medium' });
    renderPriority();
  }
  sessionLabel.textContent = 'Captured';
  setPresence({ expression: 'attentive', status: 'thinking', intensity: 0.6 }, 1400);
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
          { title: 'Start Session and type a message', why: 'Talk loop', effort: 'low' },
          { title: 'Confirm runtime auto-start', why: 'One-window workflow', effort: 'low' }
        ],
        presence: { expression: 'pleased', status: 'speaking', intensity: 0.8 },
        message: 'Offline first-use'
      };
    }
    setPresence(magic.presence || { expression: 'pleased', status: 'speaking', intensity: 0.8 }, 2400);
    sessionLabel.textContent = magic.message ? String(magic.message).slice(0, 52) : 'First-use ready';
    if (magic.moves && magic.moves.length) {
      const moves = magic.moves.map((m, i) => ({
        id: 'fu-' + i,
        title: m.title,
        meta: m.why || 'Suggestion',
        level: i === 0 ? 'medium' : 'low'
      }));
      renderPriority([...moves, ...localPriority.filter(p => !String(p.id).startsWith('fu-'))].slice(0, 6));
    }
  } finally {
    busy = false;
    firstUseBtn.disabled = false;
  }
}

async function startOrEndSession() {
  if (busy) return;
  busy = true;
  startSessionBtn.disabled = true;
  try {
    if (currentVoiceSession) {
      // End
      if (runtimeOnline) {
        await api('/voice/end', { method: 'POST', body: JSON.stringify({ session_id: currentVoiceSession }) });
      }
      currentVoiceSession = null;
      setTalkMode(false);
      sessionLabel.textContent = 'Session ended';
      setPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }, 0);
      return;
    }

    setPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 }, 0);
    sessionLabel.textContent = 'Starting session…';
    await checkRuntime();
    if (!runtimeOnline && window.aetherAPI && window.aetherAPI.ensureRuntime) {
      sessionLabel.textContent = 'Starting runtime…';
      await window.aetherAPI.ensureRuntime();
      for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 500));
        if (await checkRuntime()) break;
      }
    }
    if (!runtimeOnline) {
      sessionLabel.textContent = 'Runtime offline — try again in a few seconds';
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
      sessionLabel.textContent = (sess.session_id || '').slice(0, 16) + ' · ' + mode + ' · type below';
      setPresence(sess.presence || { expression: 'attentive', status: 'listening', intensity: 0.8 }, 0);
      setTalkMode(true);
      appendTalk('agent', 'Listening. Type a message and press Enter.');
      captureInput.focus();
      return;
    }
    sessionLabel.textContent = 'Session start failed';
    setPresence({ expression: 'concerned', status: 'idle', intensity: 0.5 }, 0);
  } finally {
    busy = false;
    startSessionBtn.disabled = false;
  }
}

async function demoComputerUse() {
  if (!runtimeOnline) {
    sessionLabel.textContent = 'Runtime offline';
    return;
  }
  setPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.6 }, 0);
  const req = await api('/computer-use/request', {
    method: 'POST',
    body: JSON.stringify({ action: 'screenshot', details: { reason: 'panel demo' } })
  });
  if (!req || !req.request_id) {
    sessionLabel.textContent = 'Request failed';
    return;
  }
  const conf = await api('/computer-use/confirm', {
    method: 'POST',
    body: JSON.stringify({ request_id: req.request_id, spoken_yes: true })
  });
  if (conf && conf.execute_on_shell && window.aetherAPI) {
    const result = await window.aetherAPI.executeComputerUse({ action: conf.action, details: conf.details });
    sessionLabel.textContent = result && result.ok ? 'Screenshot saved' : 'Execute failed';
    setPresence({ expression: 'pleased', status: 'speaking', intensity: 0.75 }, 2000);
  }
}

document.getElementById('captureBtn').addEventListener('click', onCaptureOrTalk);
captureInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') onCaptureOrTalk(); });
document.getElementById('closeBtn').addEventListener('click', () => window.close());
document.getElementById('minimizeBtn').addEventListener('click', () => window.close());
document.getElementById('switchToBookmarks').addEventListener('click', () => switchView('bookmarks'));
document.getElementById('backToPriority').addEventListener('click', () => switchView('priority'));
firstUseBtn.addEventListener('click', runFirstUse);
startSessionBtn.addEventListener('click', startOrEndSession);
document.getElementById('closeModal').addEventListener('click', closePlanModal);
document.getElementById('cancelPlan').addEventListener('click', closePlanModal);
document.getElementById('confirmMakeReal').addEventListener('click', confirmMakeReal);
presenceOrb.addEventListener('dblclick', demoComputerUse);

if (window.aetherAPI) {
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
  // Ask main to ensure runtime (auto-spawn)
  if (window.aetherAPI && window.aetherAPI.ensureRuntime) {
    sessionLabel.textContent = 'Checking runtime…';
    await window.aetherAPI.ensureRuntime();
  }
  for (let i = 0; i < 12; i++) {
    if (await checkRuntime()) break;
    await new Promise(r => setTimeout(r, 400));
  }
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
