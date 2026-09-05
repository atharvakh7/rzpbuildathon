import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  Bot,
  Layers,
  FileSpreadsheet,
  Handshake,
  BarChart3,
  Sliders,
  ShieldCheck,
  Database,
  Network,
  RotateCcw,
  CalendarClock,
} from 'lucide-react';

interface SidebarProps {
  onResetDemo?: () => void;
  resetting?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ onResetDemo, resetting = false }) => {
  const mainNav = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Revenue Risk', path: '/revenue-risk', icon: AlertTriangle },
    { name: 'Recovery Agent', path: '/recovery-agent', icon: Bot },
    { name: 'Recovery Cases', path: '/recovery-cases', icon: Layers },
    { name: 'Recovery Ledger', path: '/ledger', icon: FileSpreadsheet },
    { name: 'Promise-to-Pay', path: '/promise-to-pay', icon: Handshake },
    { name: 'Mandate Sequencer', path: '/mandates', icon: CalendarClock },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Graph View', path: '/graph', icon: Network },
  ];

  const configNav = [
    { name: 'Policies', path: '/policies', icon: Sliders },
    { name: 'Agent Permissions', path: '/agent-permissions', icon: ShieldCheck },
    { name: 'Data Simulator', path: '/simulator', icon: Database },
  ];

  return (
    <aside className="w-64 bg-[#072654] border-r border-[#1E3256] flex flex-col justify-between shrink-0 h-screen sticky top-0 shadow-xl">
      <div>
        {/* Razorpay Brand Header */}
        <div className="p-5 border-b border-[#1E3256] bg-[#051E44]/60 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#0D94FB] flex items-center justify-center text-white font-black text-xl shadow-md shadow-[#0D94FB]/25">
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                <path d="M13.976 2L4 14.502h6.588L7.843 22l12.181-12.723h-6.048z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-white">RecoverAI</span>
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#0D94FB]/20 text-[#0D94FB] border border-[#0D94FB]/40">
                  Razorpay
                </span>
              </div>
              <p className="text-[10px] text-blue-200/70 font-medium">Autonomous Revenue Recovery</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="px-3 py-4 space-y-6 overflow-y-auto max-h-[calc(100vh-170px)]">
          <div>
            <div className="px-3 mb-2.5 text-[10px] font-bold text-blue-200/50 tracking-wider uppercase">
              Financial Recovery Suite
            </div>
            <nav className="space-y-1">
              {mainNav.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-[#0D94FB] text-white font-semibold shadow-md shadow-[#0D94FB]/30'
                          : 'text-slate-300 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2.5 text-[10px] font-bold text-blue-200/50 tracking-wider uppercase">
              Risk & Governance
            </div>
            <nav className="space-y-1">
              {configNav.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-[#0D94FB] text-white font-semibold shadow-md shadow-[#0D94FB]/30'
                          : 'text-slate-300 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Footer Reset Demo & Hackathon Badge */}
      <div className="p-4 border-t border-[#1E3256] bg-[#051E44]/40 space-y-2">
        <div className="flex items-center justify-between text-[10px] text-blue-200/60 px-1 font-medium">
          <span>Razorpay Hackathon</span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live Engine
          </span>
        </div>
        <button
          onClick={onResetDemo}
          disabled={resetting}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-[#0A326B] hover:bg-[#0D3F87] border border-[#1E3256] text-xs font-medium text-blue-100 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-amber-400' : 'text-blue-300'}`} />
          <span>{resetting ? 'Resetting DB...' : 'Reset Demo Data'}</span>
        </button>
      </div>
    </aside>
  );
};
