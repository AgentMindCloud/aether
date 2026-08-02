const { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, screen, ipcMain, desktopCapturer } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let tray = null;
let isQuitting = false;
let runtimeProc = null;
let spawnedByUs = false;

let presenceState = {
  expression: 'neutral',
  status: 'idle',
  intensity: 0.5
};

function presenceKey(s) {
  if (!s) return '';
  return (s.expression || '') + '|' + (s.status || '') + '|' + Math.round((s.intensity || 0) * 100);
}

function healthCheck() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:7420/health', { timeout: 1500 }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

function spawnRuntime() {
  if (runtimeProc) return true;
  const repoRoot = path.join(__dirname, '..');
  const srcPath = path.join(repoRoot, 'src');

  // Ordered fallbacks for Windows + PATH friction
  const tryCmds = [
    { cmd: 'aether', args: ['--serve'], shell: true, env: process.env },
    { cmd: 'py', args: ['-3', '-m', 'aether.runtime', '--serve'], shell: true, env: { ...process.env, PYTHONPATH: srcPath } },
    { cmd: 'python', args: ['-m', 'aether.runtime', '--serve'], shell: true, env: { ...process.env, PYTHONPATH: srcPath } },
    { cmd: 'python3', args: ['-m', 'aether.runtime', '--serve'], shell: true, env: { ...process.env, PYTHONPATH: srcPath } },
  ];

  for (const c of tryCmds) {
    try {
      const child = spawn(c.cmd, c.args, {
        cwd: repoRoot,
        detached: true,
        stdio: 'ignore',
        shell: c.shell,
        windowsHide: true,
        env: c.env,
      });
      child.on('error', () => {
        // spawn error (ENOENT etc.) — try next
        if (runtimeProc === child) runtimeProc = null;
      });
      // Assume success until proven otherwise; health loop will confirm
      runtimeProc = child;
      runtimeProc.unref();
      spawnedByUs = true;
      console.log('[aether] Spawned runtime via', c.cmd, c.args.join(' '));
      return true;
    } catch (e) {
      console.warn('[aether] Spawn failed for', c.cmd, e.message);
      runtimeProc = null;
    }
  }
  console.error('[aether] All runtime spawn attempts failed');
  return false;
}

async function ensureRuntime() {
  if (await healthCheck()) return { ok: true, already: true };
  const spawned = spawnRuntime();
  if (!spawned) {
    return { ok: false, error: 'Could not spawn runtime (aether / py / python not found). Run: pip install -e ".[db]" then aether --serve' };
  }
  for (let i = 0; i < 25; i++) {
    await new Promise(r => setTimeout(r, 400));
    if (await healthCheck()) return { ok: true, spawned: true };
  }
  return { ok: false, error: 'Runtime did not become healthy on :7420 within ~10s. Check console or run aether --serve manually.' };
}

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: 400,
    height: 720,
    minWidth: 360,
    minHeight: 560,
    show: false,
    frame: false,
    resizable: true,
    alwaysOnTop: false,
    skipTaskbar: true,
    backgroundColor: '#0b0b0e',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');

  const x = width - 430;
  const y = Math.max(40, height - 760);
  mainWindow.setPosition(x, y);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.webContents.send('presence-update', presenceState);
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

function createTray() {
  const icon = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAXklEQVQ4T2NkYGD4z0ABYBzVMKoBBgYGBv+/f/8zMDAw/P//n4GBgYHBwcGBgYGB4f///wwMDAwMDg4ODAwMDA4ODgz////P8P//fwYGBgYGh4cHBgYGhv///zMwMDAwcHBwAACmWBf1W0s5ZwAAAABJRU5ErkJggg=='
  );
  tray = new Tray(icon);
  tray.setToolTip('Aether');
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show / Hide', click: () => toggleWindow() },
    { label: 'Focus Capture (Ctrl+Alt+A)', click: () => showAndFocus() },
    { type: 'separator' },
    { label: 'Quit', click: () => { isQuitting = true; app.quit(); } }
  ]);
  tray.setContextMenu(contextMenu);
  tray.on('click', () => toggleWindow());
  tray.on('double-click', () => showAndFocus());
}

function toggleWindow() {
  if (!mainWindow) return;
  if (mainWindow.isVisible()) mainWindow.hide();
  else { mainWindow.show(); mainWindow.focus(); }
}

function showAndFocus() {
  if (!mainWindow) return;
  mainWindow.show();
  mainWindow.focus();
  mainWindow.webContents.send('focus-capture');
}

function registerShortcuts() {
  globalShortcut.register('CommandOrControl+Alt+A', () => showAndFocus());
}

ipcMain.on('set-presence', (_e, state) => {
  const next = { ...presenceState, ...state };
  if (presenceKey(next) === presenceKey(presenceState)) return;
  presenceState = next;
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('presence-update', presenceState);
  }
});
ipcMain.handle('get-presence', () => presenceState);
ipcMain.handle('ensure-runtime', async () => ensureRuntime());

ipcMain.handle('computer-use-execute', async (_e, payload) => {
  const { action } = payload || {};
  try {
    if (action === 'screenshot') {
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: 1280, height: 720 }
      });
      if (!sources.length) return { ok: false, error: 'No screen sources' };
      const png = sources[0].thumbnail.toPNG();
      const outDir = path.join(app.getPath('userData'), 'screenshots');
      fs.mkdirSync(outDir, { recursive: true });
      const file = path.join(outDir, `shot-${Date.now()}.png`);
      fs.writeFileSync(file, png);
      return { ok: true, action: 'screenshot', path: file, size: png.length };
    }
    if (action === 'list_windows') {
      return {
        ok: true,
        action: 'list_windows',
        displays: screen.getAllDisplays().map(d => ({ id: d.id, bounds: d.bounds }))
      };
    }
    return { ok: false, error: `Action not implemented: ${action}` };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
});

app.whenReady().then(async () => {
  // Fire-and-forget ensure so UI opens fast
  ensureRuntime().catch(() => {});
  createWindow();
  createTray();
  registerShortcuts();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {});
app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('before-quit', () => {
  isQuitting = true;
  // Leave runtime running so mobile / other clients can use it later.
});
