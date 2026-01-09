import React from 'react';

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="p-4 border-b border-zinc-800">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">DecoScreen</h1>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <h2 className="text-sm font-semibold text-zinc-400 mb-4">Components</h2>
        {/* Component list will go here */}
        <div className="grid grid-cols-2 gap-2">
            <div className="bg-zinc-800 p-2 rounded cursor-pointer hover:bg-zinc-700 text-xs text-center border border-zinc-700 hover:border-zinc-500 transition-colors">Clock</div>
            <div className="bg-zinc-800 p-2 rounded cursor-pointer hover:bg-zinc-700 text-xs text-center border border-zinc-700 hover:border-zinc-500 transition-colors">CPU</div>
            <div className="bg-zinc-800 p-2 rounded cursor-pointer hover:bg-zinc-700 text-xs text-center border border-zinc-700 hover:border-zinc-500 transition-colors">GPU</div>
            <div className="bg-zinc-800 p-2 rounded cursor-pointer hover:bg-zinc-700 text-xs text-center border border-zinc-700 hover:border-zinc-500 transition-colors">RAM</div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
