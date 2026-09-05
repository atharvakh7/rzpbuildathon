import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const norm = (status || '').toUpperCase();

  let colors = 'bg-[#172744] text-[#879BBB] border-[#1E3256]';
  let dotColor = 'bg-[#879BBB]';

  if (norm === 'RECOVERED' || norm === 'SUCCESS' || norm === 'PAID' || norm === 'ALLOWED') {
    colors = 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-950/40';
    dotColor = 'bg-emerald-400 shadow-[0_0_6px_#10B981]';
  } else if (norm === 'PENDING' || norm === 'PROMISED' || norm === 'IN_PROGRESS' || norm === 'DIAGNOSED') {
    colors = 'bg-amber-950/60 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-950/40';
    dotColor = 'bg-amber-400 shadow-[0_0_6px_#F59E0B]';
  } else if (norm === 'FAILED' || norm === 'FAILURE' || norm === 'DENIED' || norm === 'MISSED' || norm === 'DISPUTED') {
    colors = 'bg-rose-950/60 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-950/40';
    dotColor = 'bg-rose-400 shadow-[0_0_6px_#EF4444]';
  } else if (norm === 'ESCALATED' || norm === 'REQUIRES_APPROVAL') {
    colors = 'bg-purple-950/60 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-950/40';
    dotColor = 'bg-purple-400 shadow-[0_0_6px_#A855F7]';
  } else if (norm === 'STOPPED') {
    colors = 'bg-[#111D33] text-slate-400 border-[#1E3256]';
    dotColor = 'bg-slate-500';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border tracking-wider uppercase font-mono ${colors} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {norm.replace(/_/g, ' ')}
    </span>
  );
};
