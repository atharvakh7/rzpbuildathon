import React, { useEffect, useState } from 'react';
import { Handshake, RefreshCw, Calendar, CheckCircle2, AlertTriangle, Plus, ChevronRight } from 'lucide-react';
import { getPromiseToPayList, updatePromiseStatus } from '../services/promiseToPay';
import { PromiseToPayItem } from '../types';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';

export const PromiseToPay: React.FC = () => {
  const [promises, setPromises] = useState<PromiseToPayItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const loadPromises = async () => {
    try {
      setLoading(true);
      const data = await getPromiseToPayList(statusFilter);
      setPromises(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPromises();
  }, [statusFilter]);

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      await updatePromiseStatus(id, newStatus);
      loadPromises();
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const totalCommitted = promises.reduce((acc, curr) => acc + (curr.amount || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Handshake className="w-6 h-6 text-[#0D94FB]" />
              <span>Promise-to-Pay (PTP) Ledger</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              B2B Receivables
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Track customer commitments, maturity dates, automated reminders, and broken promise escalations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#111D33] border border-[#1E3256] text-xs font-mono">
            <span className="text-[#879BBB]">Committed:</span>
            <span className="text-white font-bold"><Currency amount={totalCommitted} /></span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-slate-200 font-mono focus:outline-none focus:border-[#0D94FB]"
          >
            <option value="ALL">All Statuses</option>
            <option value="PROMISED">Promised</option>
            <option value="PAID">Paid</option>
            <option value="MISSED">Missed</option>
            <option value="ESCALATED">Escalated</option>
          </select>

          <button
            onClick={loadPromises}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Razorpay Commitment Table */}
      <div className="rounded-lg border border-[#1E3256] bg-[#111D33] overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#072654]/70 text-[#879BBB] font-semibold uppercase tracking-wider text-[10px] border-b border-[#1E3256]">
              <tr>
                <th className="px-6 py-3.5">Promise ID</th>
                <th className="px-6 py-3.5">Customer</th>
                <th className="px-6 py-3.5">Committed Amount</th>
                <th className="px-6 py-3.5">Promise Date</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Reminder Dispatched</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3256]/60 font-medium">
              {promises.map((p) => (
                <tr key={p.id} className="hover:bg-[#172744]/70 transition-colors">
                  <td className="px-6 py-4 font-mono text-[#879BBB]">#PTP-{p.id}</td>
                  <td className="px-6 py-4 text-white font-semibold">{p.customer_name}</td>
                  <td className="px-6 py-4 font-mono text-emerald-400 font-bold">
                    <Currency amount={p.amount} />
                  </td>
                  <td className="px-6 py-4 font-mono text-slate-300">
                    {new Date(p.promise_date).toLocaleDateString('en-IN', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-6 py-4 font-mono text-slate-300">
                    {p.reminder_sent ? (
                      <span className="text-[#0D94FB] flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Sent (SMS/Email)
                      </span>
                    ) : (
                      <span className="text-[#879BBB]">Scheduled</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {p.status === 'PROMISED' && (
                      <>
                        <button
                          onClick={() => handleUpdateStatus(p.id, 'PAID')}
                          className="px-2.5 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition-colors"
                        >
                          Mark Paid
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(p.id, 'ESCALATED')}
                          className="px-2.5 py-1 rounded bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-semibold transition-colors"
                        >
                          Escalate
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {promises.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-[#879BBB]">
                    No Promise-to-Pay commitments recorded yet.
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
