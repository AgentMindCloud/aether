// Aether shell — Build 0.1 felt presence: TTS + mic + premium talk loop

const RUNTIME_URL = 'http://127.0.0.1:7420';

const presenceOrb = document.getElementById('presenceOrb');
const presenceStatus = document.getElementById('presenceStatus');
const presenceLine = document.getElementById('presenceLine');
const captureInput = document.getElementById('captureInput');
const captureHint = document.getElementById('captureHint');
const runtimeLabel = document.getElementById('runtimeLabel');
const runtimeDot = document.getElementById('runtimeDot');
const sessionLabel = document.getElementById('sessionLabel');
const priorityList = document.getElementById('priorityList');
const bookmarkList = document.getElementById('bookmarkList');
const firstUseBtn = document.getElementById('firstUseBtn');
const startSessionBtn = document.getElementById('startSessionBtn');
const talkMessages = document.getElementById('talkMessages');
const emptySession = document.getElementById('emptySession');
const sessionBadge = document.getElementById('sessionBadge');
const talkBox = document.getElementById('talkBox');
const micBtn = document.getElementById('micBtn');
const brandSubtitle = document.getElementById('brandSubtitle');

let currentPlanBookmark = null;
let runtimeOnline = false;
let currentVoiceSession = null;
let lastPresenceKey = '';
let presenceSettleTimer = null;
let busy = false;
let speakingUtterance = null;
let recognition = null;
let isListeningMic = false;

let localPriority = [
  { id: 'p1', title: 'Start Session and speak or type', meta: 'Talk · Now', level: 'medium' },
  { id: 'p2', title: 'Optional: GROK_VOICE_API_KEY for live later', meta: 'Later', level: 'low' },
];

let localBookmarks = [
  {
    id: 'b1', category: 'Immediate', title: 'Talk path is live (TTS + text, mic when allowed)',
    source: 'Aether', score: 9.5,
    plan: ['Start Session', 'Type or use mic', 'Hear agent reply']
  },
];

/* ─── Presence ─── */
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
}

function setPresence(state, settleMs = 0) {
  renderPresence(state);
  if (window.aetherAPI) {
    try { window.aetherAPI.setPresence(state); } catch (_) {}
  }
  if (presenceSettleTimer) clearTimeout(presenceSettleTimer);
  if (settleMs > 0) {
    presenceSettleTimer = setTimeout(() => {
      if (currentVoiceSession) {
        setPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 }, 0);
        presenceLine.textContent = 'Listening…';
      } else {
        setPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }, 0);
        presenceLine.textContent = 'Ready when you are';
      }
    }, settleMs);
  }
}

/* ─── TTS (Web Speech API) ─── */
function speakText(text) {
  return new Promise((resolve) => {
    if (!window.speechSynthesis || !text) {
      resolve(false);
      return;
    }
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.02;
      u.pitch = 1.0;
      u.volume = 1.0;
      // Prefer a calm English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(v => /en-US|en-GB|English/i.test(v.lang) && /Google|Natural|Samantha|Daniel|Microsoft/i.test(v.name))
        || voices.find(v => /en/i.test(v.lang));
      if (preferred) u.voice = preferred;
      speakingUtterance = u;
      u.onend = () => { speakingUtterance = null; resolve(true); };
      u.onerror = () => { speakingUtterance = null; resolve(false); };
      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn('TTS failed', e);
      resolve(false);
    }
  });
}

function stopSpeaking() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  speakingUtterance = null;
}

/* ─── STT (Web Speech Recognition) ─── */
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const r = new SR();
  r.continuous = false;
  r.interimResults = true;
  r.lang = 'en-US';
  r.onresult = (event) => {
    let interim = '';
    let final = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) final += t;
      else interim += t;
    }
    if (interim) {
      captureInput.value = interim;
      presenceLine.textContent = interim.slice(0, 48);
    }
    if (final) {
      captureInput.value = final.trim();
      stopMic();
      onCaptureOrTalk();
    }
  };
  r.onerror = (e) => {
    console.warn('STT', e.error);
    stopMic();
    if (e.error === 'not-allowed') {
      sessionLabel.textContent = 'Mic permission denied — type instead';
    }
  };
  r.onend = () => { stopMic(); };
  return r;
}

function startMic() {
  if (!recognition) recognition = initRecognition();
  if (!recognition) {
    sessionLabel.textContent = 'Speech recognition not available in this environment';
    return;
  }
  if (!currentVoiceSession) {
    sessionLabel.textContent = 'Start Session first';
    return;
  }
  try {
    stopSpeaking();
    recognition.start();
    isListeningMic = true;
    micBtn.classList.add('active');
    setPresence({ expression: 'attentive', status: 'listening', intensity: 0.9 }, 0);
    presenceLine.textContent = 'Listening to you…';
    sessionLabel.textContent = 'Mic active — speak now';
  } catch (e) {
    console.warn('mic start', e);
  }
}

function stopMic() {
  isListeningMic = false;
  micBtn.classList.remove('active');
  try { if (recognition) recognition.stop(); } catch (_) {}
}

/* ─── API ─── */
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
  let label = runtimeOnline ? 'Runtime: connected' : 'Runtime: offline';
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

/* ─── Lists ─── */
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
      setPresence({ expression: 'pleased', status: 'speaking', intensity: 0.7 }, 1800);
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
  document.getElementById('tabPriority').classList.toggle('active', view === 'priority');
  document.getElementById('tabBookmarks').classList.toggle('active', view === 'bookmarks');
}

/* ─── Session / talk ─── */
function setTalkMode(on) {
  if (on) {
    sessionBadge.textContent = 'live';
    sessionBadge.classList.add('on');
    talkBox.classList.add('session-active');
    captureInput.placeholder = 'Speak or type… Enter sends';
    captureHint.textContent = 'Session active · Mic or Enter · End Session to stop';
    startSessionBtn.textContent = 'End Session';
    brandSubtitle.textContent = 'In session';
    if (emptySession) emptySession.style.display = 'none';
  } else {
    sessionBadge.textContent = 'off';
    sessionBadge.classList.remove('on');
    talkBox.classList.remove('session-active');
    talkMessages.innerHTML = '';
    if (emptySession) {
      talkMessages.appendChild(emptySession);
      emptySession.style.display = '';
    }
    captureInput.placeholder = 'Capture a thought or next move…';
    captureHint.textContent = 'Ctrl+Alt+A · Enter to send · Mic for voice input';
    startSessionBtn.textContent = 'Start Session';
    brandSubtitle.textContent = 'Presence';
    stopMic();
    stopSpeaking();
  }
}

function appendTalk(role, text, opts = {}) {
  if (emptySession && emptySession.parentNode) emptySession.remove();
  const div = document.createElement('div');
  div.className = 'talk-bubble ' + role + (opts.speaking ? ' speaking-now' : '');
  div.textContent = text;
  talkMessages.appendChild(div);
  talkMessages.scrollTop = talkMessages.scrollHeight;
  return div;
}

async function sendTurn(text) {
  if (!currentVoiceSession || !text) return;
  stopSpeaking();
  appendTalk('user', text);
  setPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.65 }, 0);
  presenceLine.textContent = 'Thinking…';
  sessionLabel.textContent = 'Thinking…';

  const result = await api('/voice/turn', {
    method: 'POST',
    body: JSON.stringify({ session_id: currentVoiceSession, transcript: text })
  });

  if (!result || result.error) {
    const err = result && result.error ? result.error : 'No response (is runtime up?)';
    appendTalk('agent', err);
    setPresence({ expression: 'concerned', status: 'listening', intensity: 0.6 }, 0);
    presenceLine.textContent = 'Turn failed';
    sessionLabel.textContent = 'Turn failed';
    return;
  }

  const reply = result.response || result.message || JSON.stringify(result).slice(0, 200);
  const bubble = appendTalk('agent', reply, { speaking: true });
  setPresence(result.presence || { expression: 'attentive', status: 'speaking', intensity: 0.85 }, 0);
  presenceLine.textContent = reply.slice(0, 56);
  sessionLabel.textContent = 'Turn ' + (result.turn || '') + (result.live ? ' · live' : ' · sim') +
    (result.memory_used ? ' · mem ' + result.memory_used : '');

  // Speak the reply so the user *hears* the agent
  const spoke = await speakText(reply);
  if (bubble) bubble.classList.remove('speaking-now');
  // After speech ends, settle back to listening
  const settle = spoke ? 400 : 1800;
  setPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 }, settle);
  presenceLine.textContent = 'Listening…';
}

async function onCaptureOrTalk() {
  const text = captureInput.value.trim();
  if (!text) return;
  captureInput.value = '';
  if (currentVoiceSession) {
    await sendTurn(text);
    return;
  }
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
          { title: 'Start Session and speak or type', why: 'Talk loop', effort: 'low' },
          { title: 'Confirm runtime auto-start', why: 'One-window workflow', effort: 'low' }
        ],
        presence: { expression: 'pleased', status: 'speaking', intensity: 0.8 },
        message: 'Ready. Start Session to talk.'
      };
    }
    const msg = magic.message || 'Ready. Start Session to talk.';
    setPresence(magic.presence || { expression: 'pleased', status: 'speaking', intensity: 0.8 }, 0);
    presenceLine.textContent = String(msg).slice(0, 56);
    sessionLabel.textContent = String(msg).slice(0, 52);
    await speakText(String(msg));
    setPresence({ expression: 'attentive', status: 'idle', intensity: 0.6 }, 600);
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
      stopSpeaking();
      stopMic();
      if (runtimeOnline) {
        await api('/voice/end', { method: 'POST', body: JSON.stringify({ session_id: currentVoiceSession }) });
      }
      currentVoiceSession = null;
      setTalkMode(false);
      sessionLabel.textContent = 'Session ended';
      presenceLine.textContent = 'Ready when you are';
      setPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }, 0);
      return;
    }

    setPresence({ expression: 'attentive', status: 'listening', intensity: 0.8 }, 0);
    presenceLine.textContent = 'Starting…';
    sessionLabel.textContent = 'Starting session…';
    await checkRuntime();
    if (!runtimeOnline && window.aetherAPI && window.aetherAPI.ensureRuntime) {
      sessionLabel.textContent = 'Starting runtime…';
      await window.aetherAPI.ensureRuntime();
      for (let i = 0; i < 18; i++) {
        await new Promise(r => setTimeout(r, 450));
        if (await checkRuntime()) break;
      }
    }
    if (!runtimeOnline) {
      sessionLabel.textContent = 'Runtime offline — check PATH or run: aether --serve';
      presenceLine.textContent = 'Runtime offline';
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
      sessionLabel.textContent = (sess.session_id || '').slice(0, 14) + ' · ' + mode;
      setPresence(sess.presence || { expression: 'attentive', status: 'listening', intensity: 0.8 }, 0);
      setTalkMode(true);
      const greeting = sess.greeting || 'Listening. Speak or type when ready.';
      appendTalk('agent', greeting);
      presenceLine.textContent = 'Listening…';
      await speakText(greeting);
      setPresence({ expression: 'attentive', status: 'listening', intensity: 0.75 }, 300);
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
    await speakText(result && result.ok ? 'Screenshot saved.' : 'Screenshot failed.');
  }
}

/* ─── Events ─── */
document.getElementById('captureBtn').addEventListener('click', onCaptureOrTalk);
captureInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') onCaptureOrTalk(); });
micBtn.addEventListener('click', () => {
  if (isListeningMic) stopMic();
  else startMic();
});
document.getElementById('closeBtn').addEventListener('click', () => window.close());
document.getElementById('minimizeBtn').addEventListener('click', () => window.close());
document.getElementById('tabPriority').addEventListener('click', () => switchView('priority'));
document.getElementById('tabBookmarks').addEventListener('click', () => switchView('bookmarks'));
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
  if (e.key === 'Escape') {
    closePlanModal();
    stopMic();
    stopSpeaking();
  }
});

// Chrome loads voices async
if (window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

(async () => {
  if (window.aetherAPI && window.aetherAPI.ensureRuntime) {
    sessionLabel.textContent = 'Checking runtime…';
    await window.aetherAPI.ensureRuntime();
  }
  for (let i = 0; i < 14; i++) {
    if (await checkRuntime()) break;
    await new Promise(r => setTimeout(r, 400));
  }
  if (runtimeOnline) {
    const pri = await api('/priority');
    const bms = await api('/bookmarks');
    if (pri && pri.items) localPriority = pri.items;
    if (bms && bms.items) localBookmarks = bms.items;
  } else {
    sessionLabel.textContent = 'Runtime offline — will auto-start on Start Session';
  }
  renderPriority();
  renderBookmarks();
  setInterval(checkRuntime, 8000);
})();
