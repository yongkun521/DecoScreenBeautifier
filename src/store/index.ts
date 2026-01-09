import { create } from 'zustand';
import { BaseWidget, AppConfig, Template, WidgetType } from '../types';

interface AppState {
  config: AppConfig;
  widgets: BaseWidget[];
  templates: Template[];
  selectedWidgetId: string | null;
  
  // Actions
  setConfig: (config: Partial<AppConfig>) => void;
  addWidget: (widget: BaseWidget) => void;
  updateWidget: (id: string, updates: Partial<BaseWidget>) => void;
  removeWidget: (id: string) => void;
  selectWidget: (id: string | null) => void;
  setWidgets: (widgets: BaseWidget[]) => void;
  loadTemplate: (templateId: string) => void;
}

const DEFAULT_CONFIG: AppConfig = {
  version: '1.0.0',
  autoLaunch: false,
  minimizeToTray: false,
  screenSize: { width: 1920, height: 480 }, // Example secondary screen
  theme: 'dark',
};

export const useAppStore = create<AppState>((set, get) => ({
  config: DEFAULT_CONFIG,
  widgets: [
    {
      id: 'init-hw-1',
      type: WidgetType.HARDWARE_MONITOR,
      position: { x: 50, y: 50 },
      size: { width: 300, height: 200 },
      style: {
        opacity: 1,
        zIndex: 1
      }
    },
    {
      id: 'init-clock-1',
      type: WidgetType.CLOCK,
      position: { x: 400, y: 50 },
      size: { width: 300, height: 200 },
      style: {
        opacity: 1,
        zIndex: 1
      }
    }
  ],
  templates: [],
  selectedWidgetId: null,

  setConfig: (newConfig) => set((state) => ({ config: { ...state.config, ...newConfig } })),
  
  addWidget: (widget) => set((state) => ({ widgets: [...state.widgets, widget] })),
  
  updateWidget: (id, updates) => set((state) => ({
    widgets: state.widgets.map((w) => (w.id === id ? { ...w, ...updates } : w)),
  })),
  
  removeWidget: (id) => set((state) => ({
    widgets: state.widgets.filter((w) => w.id !== id),
    selectedWidgetId: state.selectedWidgetId === id ? null : state.selectedWidgetId,
  })),
  
  selectWidget: (id) => set({ selectedWidgetId: id }),
  
  setWidgets: (widgets) => set({ widgets }),
  
  loadTemplate: (templateId) => {
    const template = get().templates.find(t => t.id === templateId);
    if (template) {
      set({ widgets: template.widgets, config: { ...get().config, screenSize: template.screenSize } });
    }
  },
}));
