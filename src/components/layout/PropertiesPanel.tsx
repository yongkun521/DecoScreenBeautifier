import React from 'react';
import { useAppStore } from '../../store';

const PropertiesPanel: React.FC = () => {
  const { selectedWidgetId } = useAppStore();

  return (
    <div className="w-72 bg-zinc-900 border-l border-zinc-800 flex flex-col">
       <div className="p-4 border-b border-zinc-800">
        <h2 className="font-semibold text-zinc-200">Properties</h2>
      </div>
      <div className="p-4">
        {!selectedWidgetId ? (
            <p className="text-zinc-500 text-sm">Select a component to edit</p>
        ) : (
            <div>
                {/* Properties form */}
                <p className="text-zinc-300">Widget ID: {selectedWidgetId}</p>
            </div>
        )}
      </div>
    </div>
  );
};

export default PropertiesPanel;
