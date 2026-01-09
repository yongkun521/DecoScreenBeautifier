/// <reference types="vite/client" />

interface ElectronAPI {
  ping: () => Promise<string>;
  getSystemStats: () => Promise<{
    cpu: {
      manufacturer: string;
      brand: string;
      speed: string;
      cores: number;
      usage: number;
      temp: number;
    };
    memory: {
      total: number;
      free: number;
      used: number;
      active: number;
      available: number;
    };
    gpu: {
      model: string;
      vram: number;
      usage: number;
    }[];
  } | null>;
}

interface Window {
  electronAPI: ElectronAPI;
}
