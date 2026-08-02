const { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, screen, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;
let tray = null;
let isQuitting = false;

// Simple presence state shared with renderer
let presenceState = {
  expression: 'neutral',
  status: 'idle',
  intensity: 0.5
};

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: 380,
    height: 520,
    minWidth: 340,
    minHeight: 420,
    show: false,
    frame: false,
    transparent: false,
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

  // Position near bottom-right
  const x = width - 410;
  const y = Math.max(40, height - 560);
  mainWindow.setPosition(x, y);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // Push initial presence
    mainWindow.webContents.send('presence-update', presenceState);
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  // Minimal placeholder icon (16x16)
  const icon = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAXklEQVQ4T2NkYGD4z0ABYBzVMKoBBgYGBv+/f/8zMDAw/P//n4GBgYHBwcGBgYGB4f///wwMDAwMDg4ODAwMDA4ODgz////P8P//fwYGBgYGh4cHBgYGhv///zMwMDAwcHBwAACmWBf1W0s5ZwAAAABJRU5ErkJggg=='
  );

  tray = new Tray(icon);
  tray.setToolTip('Aether');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show / Hide',
      click: () => toggleWindow()
    },
    {
      label: 'Focus Capture (Ctrl+Alt+A)',
      click: () => showAndFocus()
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);

  tray.on('click', () => toggleWindow());
  tray.on('double-click', () => showAndFocus());
}

function toggleWindow() {
  if (!mainWindow) return;
  if (mainWindow.isVisible()) {
    mainWindow.hide();
  } else {
    mainWindow.show();
    mainWindow.focus();
  }
}

function showAndFocus() {
  if (!mainWindow) return;
  mainWindow.show();
  mainWindow.focus();
  mainWindow.webContents.send('focus-capture');
}

function registerShortcuts() {
  const ret = globalShortcut.register('CommandOrControl+Alt+A', () => {
    showAndFocus();
  });
  if (!ret) {
    console.log('Global shortcut registration failed');
  }
}

// IPC: presence updates from renderer or future runtime bridge
ipcMain.on('set-presence', (_event, state) => {
  presenceState = { ...presenceState, ...state };
  if (mainWindow) {
    mainWindow.webContents.send('presence-update', presenceState);
  }
});

ipcMain.handle('get-presence', () => presenceState);

app.whenReady().then(() => {
  createWindow();
  createTray();
  registerShortcuts();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // stay in tray on non-mac
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('before-quit', () => {
  isQuitting = true;
});
