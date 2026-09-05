import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: string;
    positive?: boolean;
  };
  highlight?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  highlight = false,
}) => {
  return (
    <div
      className={`relative overflow-hidden rounded-lg p-5 border transition-all duration-200 ${
        highlight
          ? 'bg-gradient-to-br from-[#0D94FB]/15 via-[#111D33] to-[#111D33] border-[#0D94FB]/50 shadow-lg shadow-[#0D94FB]/10'
          : 'bg-[#111D33] border-[#1E3256] hover:border-[#2A436E]'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[#879BBB] uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="p-2 rounded-md bg-[#172744] text-[#0D94FB]">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">{value}</div>
        {trend && (
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              trend.positive
                ? 'text-emerald-400 bg-emerald-950/70 border border-emerald-500/30'
                : 'text-rose-400 bg-rose-950/70 border border-rose-500/30'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-xs text-[#879BBB]">{subtitle}</p>}
    </div>
  );
};
