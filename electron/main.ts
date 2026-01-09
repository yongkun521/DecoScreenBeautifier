import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import si from 'systeminformation';

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow: BrowserWindow | null = null;

const createWindow = () => {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    // frame: true, // Standard frame for now
    // titleBarStyle: 'hidden', // For custom title bar if needed
  });

  // Test environment variable to load dev server or build
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
};

app.on('ready', () => {
  createWindow();

  // IPC Handlers
  ipcMain.handle('ping', () => 'pong');

  ipcMain.handle('get-system-stats', async () => {
    try {
      const [cpu, mem, currentLoad, gpu] = await Promise.all([
        si.cpu(),
        si.mem(),
        si.currentLoad(),
        si.graphics(),
      ]);

      return {
        cpu: {
          manufacturer: cpu.manufacturer,
          brand: cpu.brand,
          speed: cpu.speed,
          cores: cpu.cores,
          usage: currentLoad.currentLoad,
          temp: 0 // Temp often requires admin rights or specific drivers, leaving as 0 for now
        },
        memory: {
          total: mem.total,
          free: mem.free,
          used: mem.used,
          active: mem.active,
          available: mem.available,
        },
        gpu: gpu.controllers.map(g => ({
          model: g.model,
          vram: g.vram,
          usage: g.memoryUsed // Note: GPU usage isn't always available via si on all platforms
        }))
      };
    } catch (error) {
      console.error('Error getting system stats:', error);
      return null;
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

