import React from 'react';
import { Bot, Shield, Zap } from 'lucide-react';

interface NavbarProps {
  title?: string;
  subtitle?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title, subtitle }) => {
  return (
    <header className="h-16 border-b border-[#1E3256] bg-[#072654]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      <div className="flex items-center gap-4">
        {title ? (
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">{title}</h1>
            {subtitle && <p className="text-xs text-[#879BBB]">{subtitle}</p>}
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#111D33] border border-[#1E3256] text-xs font-mono text-slate-300">
              <span className="text-[10px] text-[#879BBB] uppercase font-bold tracking-wider">MID:</span>
              <span className="text-[#0D94FB] font-semibold">rzp_live_recovAI</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-[#879BBB]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>Webhooks Connected</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Razorpay Environment Pill */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 text-xs font-medium font-mono shadow-sm shadow-emerald-950/50">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]" />
          <span className="font-bold tracking-wider text-[11px]">RAZORPAY LIVE</span>
        </div>

        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-[#0D94FB]/15 border border-[#0D94FB]/30 text-[#0D94FB] text-xs font-medium">
          <Shield className="w-3.5 h-3.5" />
          <span>Guardrails Enforced</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-[#111D33] border border-[#1E3256] text-slate-300 text-xs font-mono">
          <Zap className="w-3 h-3 text-amber-400" />
          <span>ERV Engine 2.0</span>
        </div>
      </div>
    </header>
  );
};
