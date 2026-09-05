import React, { useEffect, useState } from 'react';
import { FileSpreadsheet, RefreshCw, Filter, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { getLedgerEntries } from '../services/ledger';
import { LedgerEntry } from '../types';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';

export const RecoveryLedger: React.FC = () => {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadLedger = async () => {
    try {
      setLoading(true);
      const data = await getLedgerEntries(undefined, 300);
      setEntries(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLedger();
  }, []);

  const totalRecovered = entries.reduce((acc, curr) => acc + (curr.amount_recovered || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <FileSpreadsheet className="w-6 h-6 text-[#0D94FB]" />
              <span>Recovery Settlement Ledger</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Audit Log
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Immutable financial audit trail recording every autonomous intervention, policy evaluation, and realized settlement.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#111D33] border border-[#1E3256] text-xs font-mono">
            <span className="text-[#879BBB]">Total Logged:</span>
            <span className="text-emerald-400 font-bold"><Currency amount={totalRecovered} /></span>
          </div>
          <button
            onClick={loadLedger}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
            <span>Refresh Ledger</span>
          </button>
        </div>
      </div>

      {/* Razorpay Settlement Table */}
      <div className="rounded-lg border border-[#1E3256] bg-[#111D33] overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#072654]/70 text-[#879BBB] font-semibold uppercase tracking-wider text-[10px] border-b border-[#1E3256]">
              <tr>
                <th className="px-5 py-3.5">Timestamp</th>
                <th className="px-5 py-3.5">Case ID</th>
                <th className="px-5 py-3.5">Customer</th>
                <th className="px-5 py-3.5">Amount at Risk</th>
                <th className="px-5 py-3.5">Intervention Executed</th>
                <th className="px-5 py-3.5">Expected Value (ERV)</th>
                <th className="px-5 py-3.5">Policy Check</th>
                <th className="px-5 py-3.5">Outcome</th>
                <th className="px-5 py-3.5">Recovered Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3256]/60 font-medium">
              {entries.map((item) => (
                <tr key={item.id} className="hover:bg-[#172744]/70 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-[#879BBB] whitespace-nowrap">
                    {new Date(item.created_at).toLocaleString('en-IN', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-300">#{item.case_id}</td>
                  <td className="px-5 py-3.5 text-white font-semibold">{item.customer_name}</td>
                  <td className="px-5 py-3.5 font-mono text-slate-200">
                    <Currency amount={item.amount_at_risk} />
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="font-mono text-[#0D94FB] font-semibold text-[11px] px-2 py-0.5 rounded bg-[#0D94FB]/10 border border-[#0D94FB]/20">
                      {item.selected_action?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-200">
                    <Currency amount={item.expected_recovery_value || 0} />
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={item.policy_result || 'ALLOWED'} />
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={item.execution_result || 'SUCCESS'} />
                  </td>
                  <td className="px-5 py-3.5 font-mono font-bold text-emerald-400">
                    <Currency amount={item.amount_recovered} />
                  </td>
                </tr>
              ))}
              {entries.length === 0 && !loading && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-[#879BBB]">
                    No ledger entries recorded yet. Run the recovery agent or batch simulator.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
