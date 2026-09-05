import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Search, Filter, RefreshCw, ChevronRight } from 'lucide-react';
import { getRecoveryCases } from '../services/recovery';
import { RecoveryCaseListItem } from '../types';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';

export const RecoveryCases: React.FC = () => {
  const [cases, setCases] = useState<RecoveryCaseListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');
  const navigate = useNavigate();

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await getRecoveryCases(statusFilter, typeFilter, 500);
      setCases(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, typeFilter]);

  const filtered = cases.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.customer_name.toLowerCase().includes(q) ||
      c.id.toString().includes(q) ||
      (c.root_cause && c.root_cause.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Layers className="w-6 h-6 text-[#0D94FB]" />
              <span>Recovery Cases</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Engine
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Active and resolved lifecycle records managed autonomously by the ERV recovery loop.
          </p>
        </div>

        <button
          onClick={loadCases}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters and Search */}
      <div className="p-4 rounded-lg bg-[#111D33] border border-[#1E3256] flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#879BBB] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search cases by customer, case ID, or root cause..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-white placeholder-[#879BBB] focus:outline-none focus:border-[#0D94FB] transition-colors"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-[#879BBB]">
            <Filter className="w-3.5 h-3.5" />
            <span>Category:</span>
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-slate-200 focus:outline-none focus:border-[#0D94FB] font-mono"
          >
            <option value="ALL">All Categories</option>
            <option value="PAYMENT">Payment Failures</option>
            <option value="CHECKOUT">Checkout Drop-offs</option>
            <option value="RECEIVABLES">B2B Receivables</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-slate-200 focus:outline-none focus:border-[#0D94FB] font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="DIAGNOSED">Diagnosed</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RECOVERED">Recovered</option>
            <option value="ESCALATED">Escalated</option>
            <option value="STOPPED">Stopped</option>
          </select>
        </div>
      </div>

      {/* Razorpay Styled Table */}
      <div className="rounded-lg border border-[#1E3256] bg-[#111D33] overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#072654]/60 text-[#879BBB] font-semibold uppercase tracking-wider text-[10px] border-b border-[#1E3256]">
              <tr>
                <th className="px-6 py-3.5">ID</th>
                <th className="px-6 py-3.5">Customer</th>
                <th className="px-6 py-3.5">Category</th>
                <th className="px-6 py-3.5">Amount at Risk</th>
                <th className="px-6 py-3.5">Amount Recovered</th>
                <th className="px-6 py-3.5">Attempts</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3256]/60 font-medium">
              {filtered.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/recovery-agent?caseId=${c.id}`)}
                  className="hover:bg-[#172744]/70 transition-colors cursor-pointer group"
                >
                  <td className="px-6 py-4 font-mono text-[#879BBB]">#{c.id}</td>
                  <td className="px-6 py-4 text-white font-semibold">
                    <span>{c.customer_name}</span>
                  </td>
                  <td className="px-6 py-4 font-mono uppercase text-slate-300 text-[11px]">{c.recovery_type}</td>
                  <td className="px-6 py-4 font-mono text-slate-200">
                    <Currency amount={c.amount_at_risk} />
                  </td>
                  <td className="px-6 py-4 font-mono text-emerald-400 font-bold">
                    <Currency amount={c.amount_recovered} />
                  </td>
                  <td className="px-6 py-4 font-mono text-[#879BBB]">{c.attempt_count}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="px-6 py-4 text-right text-[#879BBB] group-hover:text-[#0D94FB] transition-colors">
                    <span className="inline-flex items-center gap-1 text-xs font-semibold">
                      Inspect <ChevronRight className="w-3.5 h-3.5 inline group-hover:translate-x-0.5 transition-transform" />
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-[#879BBB]">
                    No cases match the selected filters.
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
