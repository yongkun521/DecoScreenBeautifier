import React from 'react';
import Draggable from 'react-draggable';
import { Resizable } from 're-resizable';
import clsx from 'clsx';
import { useAppStore } from '../../store';
import { HardwareMonitor } from '../widgets/HardwareMonitor';
import { Clock } from '../widgets/Clock';

const Canvas: React.FC = () => {
  const { config, widgets, updateWidget, selectWidget, selectedWidgetId } = useAppStore();

  const renderWidget = (widget: any) => {
    switch (widget.type) {
      case 'hardware-monitor':
        return <HardwareMonitor className="w-full h-full" />;
      case 'clock':
        return <Clock className="w-full h-full" />;
      default:
        return <div className="p-2 border border-dashed border-white/20 w-full h-full flex items-center justify-center">{widget.type}</div>;
    }
  }

  return (
    <div className="flex-1 bg-zinc-950 flex items-center justify-center p-8 overflow-auto" onClick={() => selectWidget(null)}>
      <div 
        className="bg-black relative shadow-2xl border border-zinc-800 transition-all duration-300 overflow-hidden"
        style={{
          width: config.screenSize.width,
          height: config.screenSize.height,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {widgets.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center text-zinc-600">
                Drag components here
            </div>
        )}
        {widgets.map(w => (
            <Draggable
                key={w.id}
                position={{ x: w.position.x, y: w.position.y }}
                onStop={(e, data) => {
                    updateWidget(w.id, { position: { x: data.x, y: data.y } });
                }}
                onStart={(e) => {
                    selectWidget(w.id);
                }}
            >
                <div style={{ position: 'absolute', zIndex: w.style.zIndex }}>
                    <Resizable
                        size={{ width: w.size.width, height: w.size.height }}
                        onResizeStop={(e, direction, ref, d) => {
                            updateWidget(w.id, {
                                size: {
                                    width: w.size.width + d.width,
                                    height: w.size.height + d.height,
                                }
                            });
                        }}
                        className={clsx(
                            "relative group",
                            selectedWidgetId === w.id && "ring-1 ring-cyan-500"
                        )}
                        onClick={(e) => {
                            e.stopPropagation();
                            selectWidget(w.id);
                        }}
                    >
                        {renderWidget(w)}
                    </Resizable>
                </div>
            </Draggable>
        ))}
      </div>
    </div>
  );
};

export default Canvas;
