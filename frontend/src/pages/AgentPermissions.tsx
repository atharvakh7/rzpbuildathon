import React, { useEffect, useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, Ban, RefreshCw, Shield } from 'lucide-react';
import { getAgentPermissions } from '../services/policies';
import { AgentPermissions as PermissionsType } from '../types';

export const AgentPermissions: React.FC = () => {
  const [permissions, setPermissions] = useState<PermissionsType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    getAgentPermissions().then((data) => {
      setPermissions(data);
      setLoading(false);
    });
  }, []);

  if (loading && !permissions) {
    return (
      <div className="flex items-center justify-center h-64 text-[#879BBB]">
        <RefreshCw className="w-6 h-6 animate-spin text-[#0D94FB] mr-3" />
        <span>Loading permissions matrix...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[#0D94FB]" />
            <span>Bounded Autonomy Matrix</span>
          </h1>
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
            Razorpay Governance
          </span>
        </div>
        <p className="text-xs text-[#879BBB] mt-1">
          Rigid permissions boundary defining where RecoverAI acts autonomously, where human intervention is required, and what is strictly prohibited.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Autonomous */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-emerald-500/40 space-y-4 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center gap-3 border-b border-[#1E3256] pb-3">
            <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Fully Autonomous</h2>
              <p className="text-[11px] text-emerald-400">Zero human intervention needed</p>
            </div>
          </div>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {permissions?.autonomous.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#10B981] mt-1.5 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Human Approval Required */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-purple-500/40 space-y-4 shadow-lg shadow-purple-950/20">
          <div className="flex items-center gap-3 border-b border-[#1E3256] pb-3">
            <div className="p-2 rounded-md bg-purple-500/10 text-purple-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Human Escalation</h2>
              <p className="text-[11px] text-purple-400">Escalates to operator review</p>
            </div>
          </div>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {permissions?.requires_approval.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shadow-[0_0_6px_#A855F7] mt-1.5 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Strictly Forbidden */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-rose-500/40 space-y-4 shadow-lg shadow-rose-950/20">
          <div className="flex items-center gap-3 border-b border-[#1E3256] pb-3">
            <div className="p-2 rounded-md bg-rose-500/10 text-rose-400">
              <Ban className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Strictly Prohibited</h2>
              <p className="text-[11px] text-rose-400">Authoritative hard stops</p>
            </div>
          </div>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {permissions?.never_allowed.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shadow-[0_0_6px_#EF4444] mt-1.5 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
