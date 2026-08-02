const { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, screen, ipcMain, desktopCapturer } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let tray = null;
let isQuitting = false;

let presenceState = {
  expression: 'neutral',
  status: 'idle',
  intensity: 0.5
};

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: 400,
    height: 640,
    minWidth: 360,
    minHeight: 480,
    show: false,
    frame: false,
    resizable: true,
    alwaysOnTop: false,
    skipTaskbar: true,
    backgroundColor: '#0a0a0c',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');

  const x = width - 430;
  const y = Math.max(40, height - 680);
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

// Presence
ipcMain.on('set-presence', (_e, state) => {
  presenceState = { ...presenceState, ...state };
  if (mainWindow) mainWindow.webContents.send('presence-update', presenceState);
});
ipcMain.handle('get-presence', () => presenceState);

// P2: Real computer-use surfaces (gated by runtime confirmation)
ipcMain.handle('computer-use-execute', async (_e, payload) => {
  const { action, details } = payload || {};
  try {
    if (action === 'screenshot') {
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: 1280, height: 720 }
      });
      if (!sources.length) return { ok: false, error: 'No screen sources' };
      const primary = sources[0];
      const png = primary.thumbnail.toPNG();
      const outDir = path.join(app.getPath('userData'), 'screenshots');
      fs.mkdirSync(outDir, { recursive: true });
      const file = path.join(outDir, `shot-${Date.now()}.png`);
      fs.writeFileSync(file, png);
      return { ok: true, action: 'screenshot', path: file, size: png.length };
    }
    if (action === 'list_windows') {
      // Limited without extra native modules — return display info
      const displays = screen.getAllDisplays().map(d => ({
        id: d.id,
        bounds: d.bounds,
        scaleFactor: d.scaleFactor
      }));
      return { ok: true, action: 'list_windows', displays };
    }
    return { ok: false, error: `Action not implemented in shell yet: ${action}` };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
});

app.whenReady().then(() => {
  createWindow();
  createTray();
  registerShortcuts();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {});
app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('before-quit', () => { isQuitting = true; });
