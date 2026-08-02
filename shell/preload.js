const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aetherAPI', {
  onFocusCapture: (callback) => ipcRenderer.on('focus-capture', callback),
  onPresenceUpdate: (callback) => ipcRenderer.on('presence-update', callback),
  setPresence: (state) => ipcRenderer.send('set-presence', state),
  getPresence: () => ipcRenderer.invoke('get-presence'),
  executeComputerUse: (payload) => ipcRenderer.invoke('computer-use-execute', payload)
});
