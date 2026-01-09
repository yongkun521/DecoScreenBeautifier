import React from 'react';
import Sidebar from './Sidebar';
import Canvas from './Canvas';
import PropertiesPanel from './PropertiesPanel';

const MainLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-screen bg-zinc-900 text-white overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col relative overflow-hidden">
         {/* Toolbar could go here */}
         <Canvas />
      </div>
      <PropertiesPanel />
    </div>
  );
};

export default MainLayout;
