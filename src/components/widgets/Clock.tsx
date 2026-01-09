import React, { useEffect, useState } from 'react';
import clsx from 'clsx';

interface ClockProps {
  className?: string;
  style?: React.CSSProperties;
}

export const Clock: React.FC<ClockProps> = ({ className, style }) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const hours = time.getHours().toString().padStart(2, '0');
  const minutes = time.getMinutes().toString().padStart(2, '0');
  const seconds = time.getSeconds().toString().padStart(2, '0');

  return (
    <div className={clsx("flex flex-col items-center justify-center w-full h-full text-white bg-black/20 backdrop-blur-sm rounded-xl border border-white/5", className)} style={style}>
      <div className="text-6xl font-bold tracking-wider font-mono" style={{ textShadow: '0 0 20px rgba(255,255,255,0.5)' }}>
        {hours}:{minutes}
      </div>
      <div className="text-xl text-white/70 mt-2 font-light">
        {seconds}
      </div>
      <div className="text-sm text-white/50 mt-1 uppercase tracking-widest">
        {time.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
      </div>
    </div>
  );
};
