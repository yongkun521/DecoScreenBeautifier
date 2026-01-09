export enum WidgetType {
  HARDWARE_MONITOR = 'hardware-monitor',
  CPU_MONITOR = 'cpu-monitor',
  GPU_MONITOR = 'gpu-monitor',
  RAM_MONITOR = 'ram-monitor',
  TEMP_MONITOR = 'temp-monitor',
  CLOCK = 'clock',
  AUDIO_VISUALIZER = 'audio-visualizer',
  IMAGE_STICKER = 'image-sticker',
  GIF_STICKER = 'gif-sticker',
  BACKGROUND = 'background'
}

export interface WidgetStyle {
  theme?: string;
  color?: string;
  backgroundColor?: string;
  opacity?: number;
  fontSize?: number;
  fontFamily?: string;
  borderRadius?: number;
  animation?: string;
  zIndex?: number;
}

export interface BaseWidget {
  id: string;
  type: WidgetType;
  position: { x: number; y: number };
  size: { width: number; height: number };
  style: WidgetStyle;
  data?: any;
  title?: string; // Optional title for display
}

export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  screenSize: {
    width: number;
    height: number;
  };
  widgets: BaseWidget[];
  background?: {
    type: 'color' | 'image' | 'gradient';
    value: string;
  };
}

export interface AppConfig {
  version: string;
  autoLaunch: boolean;
  minimizeToTray: boolean;
  screenSize: {
    width: number;
    height: number;
  };
  currentTemplateId?: string;
  theme: 'dark' | 'light';
}
