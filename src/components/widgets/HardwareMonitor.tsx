import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, MemoryStick } from 'lucide-react';
import clsx from 'clsx';

interface HardwareStats {
  cpu: {
    usage: number;
    temp: number;
  };
  memory: {
    used: number;
    total: number;
  };
}

interface HardwareMonitorProps {
  className?: string;
  style?: React.CSSProperties;
}

export const HardwareMonitor: React.FC<HardwareMonitorProps> = ({ className, style }) => {
  const [stats, setStats] = useState<HardwareStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        if (window.electronAPI) {
          const data = await window.electronAPI.getSystemStats();
          if (data) {
            setStats({
              cpu: {
                usage: data.cpu.usage,
                temp: data.cpu.temp,
              },
              memory: {
                used: data.memory.used,
                total: data.memory.total,
              },
            });
          }
        } else {
          // Mock data for browser development
          setStats({
            cpu: { usage: Math.random() * 100, temp: 45 + Math.random() * 20 },
            memory: { used: 8 * 1024 * 1024 * 1024, total: 16 * 1024 * 1024 * 1024 },
          });
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div className="text-white/50 text-sm p-4">Loading stats...</div>;

  const memUsagePercent = (stats.memory.used / stats.memory.total) * 100;

  return (
    <div className={clsx("p-4 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 text-white w-full h-full flex flex-col justify-center gap-4", className)} style={style}>
      {/* CPU Section */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-cyan-400 font-medium uppercase tracking-wider">
          <div className="flex items-center gap-1">
            <Cpu size={14} />
            <span>CPU</span>
          </div>
          <span>{stats.cpu.usage.toFixed(1)}%</span>
        </div>
        <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
            initial={{ width: 0 }}
            animate={{ width: `${stats.cpu.usage}%` }}
            transition={{ type: "spring", stiffness: 50 }}
          />
        </div>
      </div>

      {/* Memory Section */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-purple-400 font-medium uppercase tracking-wider">
          <div className="flex items-center gap-1">
            <MemoryStick size={14} />
            <span>RAM</span>
          </div>
          <span>{memUsagePercent.toFixed(1)}%</span>
        </div>
        <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"
            initial={{ width: 0 }}
            animate={{ width: `${memUsagePercent}%` }}
            transition={{ type: "spring", stiffness: 50 }}
          />
        </div>
      </div>
    </div>
  );
};
