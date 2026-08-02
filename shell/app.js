// Aether shell — presence surface + capture (P0)

const presenceOrb = document.getElementById('presenceOrb');
const presenceStatus = document.getElementById('presenceStatus');
const presenceExpression = document.getElementById('presenceExpression');
const captureInput = document.getElementById('captureInput');
const runtimeLabel = document.getElementById('runtimeLabel');
const sessionLabel = document.getElementById('sessionLabel');

function applyPresence(state) {
  if (!state) return;
  const { expression = 'neutral', status = 'idle', intensity = 0.5 } = state;

  presenceOrb.className = 'presence-orb ' + status;
  presenceStatus.textContent = status;
  presenceExpression.textContent = expression + ' · ' + Math.round(intensity * 100) + '%';
}

// Listen for presence updates from main process
if (window.aetherAPI) {
  window.aetherAPI.onPresenceUpdate((event, state) => {
    applyPresence(state);
  });

  window.aetherAPI.onFocusCapture(() => {
    captureInput.focus();
    captureInput.select();
  });

  // Initial fetch
  window.aetherAPI.getPresence().then(applyPresence);
}

// Capture
function addCapture() {
  const text = captureInput.value.trim();
  if (!text) return;
  console.log('[Aether] Captured:', text);
  captureInput.value = '';
  // Future: push to Priority / runtime via IPC
  sessionLabel.textContent = 'Captured · just now';
  setTimeout(() => { sessionLabel.textContent = 'No active session'; }, 2500);
}

document.getElementById('captureBtn').addEventListener('click', addCapture);
captureInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') addCapture();
});

// Buttons
document.getElementById('closeBtn').addEventListener('click', () => {
  // Hide is handled by main process on close event
  window.close();
});
document.getElementById('minimizeBtn').addEventListener('click', () => {
  window.close();
});

document.getElementById('startSessionBtn').addEventListener('click', () => {
  // P0 stub — will call runtime via IPC next
  applyPresence({ expression: 'attentive', status: 'listening', intensity: 0.7 });
  sessionLabel.textContent = 'Session: reactive (stub)';
  runtimeLabel.textContent = 'Runtime: waiting for live bridge';
});

document.getElementById('openDemoBtn').addEventListener('click', () => {
  // Simulate the demo loop presence states
  applyPresence({ expression: 'neutral', status: 'idle', intensity: 0.5 });
  setTimeout(() => applyPresence({ expression: 'attentive', status: 'listening', intensity: 0.7 }), 600);
  setTimeout(() => applyPresence({ expression: 'thoughtful', status: 'thinking', intensity: 0.65 }), 1600);
  setTimeout(() => applyPresence({ expression: 'attentive', status: 'speaking', intensity: 0.8 }), 2800);
  setTimeout(() => applyPresence({ expression: 'calm', status: 'idle', intensity: 0.5 }), 4200);
  sessionLabel.textContent = 'Demo loop completed';
  runtimeLabel.textContent = 'Runtime: offline demo ok';
});

// Keyboard
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'a') {
    e.preventDefault();
    captureInput.focus();
  }
});
