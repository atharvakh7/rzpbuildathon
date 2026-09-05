import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, RefreshCw, ArrowUpDown, Zap } from 'lucide-react';
import { getRevenueRiskQueue } from '../services/recovery';
import { RevenueRiskItem } from '../types';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';

export const RevenueRisk: React.FC = () => {
  const [items, setItems] = useState<RevenueRiskItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const navigate = useNavigate();

  const loadRisks = async () => {
    try {
      setLoading(true);
      const data = await getRevenueRiskQueue(typeFilter, statusFilter, 500);
      setItems(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRisks();
  }, [typeFilter, statusFilter]);

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.customer_name.toLowerCase().includes(q) ||
      item.id.toString().includes(q) ||
      (item.root_cause && item.root_cause.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Zap className="w-6 h-6 text-[#0D94FB]" />
              <span>Revenue Risk Detection</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Ingestion
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Prioritized stream of revenue slipping away across Payments, Checkouts, and Overdue Receivables.
          </p>
        </div>

        <button
          onClick={loadRisks}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Filter and Search Controls */}
      <div className="p-4 rounded-lg bg-[#111D33] border border-[#1E3256] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#879BBB] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by customer name, case ID, or root cause..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-white placeholder-[#879BBB] focus:outline-none focus:border-[#0D94FB]"
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
            <option value="CHECKOUT">Checkout Abandonment</option>
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

      {/* Main Table */}
      <div className="rounded-lg border border-[#1E3256] bg-[#111D33] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B1528] text-[#879BBB] font-semibold uppercase tracking-wider text-[10px] border-b border-[#1E3256]">
              <tr>
                <th className="px-6 py-3.5">Case ID</th>
                <th className="px-6 py-3.5">Customer</th>
                <th className="px-6 py-3.5">Amount at Risk</th>
                <th className="px-6 py-3.5">Category</th>
                <th className="px-6 py-3.5">Diagnosed Cause</th>
                <th className="px-6 py-3.5">Risk Score</th>
                <th className="px-6 py-3.5">Recovery Probability</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Autonomous Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3256]/60 font-medium">
              {filteredItems.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => navigate(`/recovery-agent?caseId=${item.id}`)}
                  className="hover:bg-[#172744]/60 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4 font-mono text-slate-300">#{item.id}</td>
                  <td className="px-6 py-4 text-white font-semibold">{item.customer_name}</td>
                  <td className="px-6 py-4 font-mono font-bold text-emerald-400">
                    <Currency amount={item.amount} />
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#0B1528] text-slate-300 border border-[#1E3256] font-mono uppercase">
                      {item.recovery_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {item.root_cause ? item.root_cause.replace(/_/g, ' ') : <span className="text-[#879BBB] italic">Unanalyzed</span>}
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono px-2 py-0.5 rounded-md bg-rose-950/60 text-rose-300 border border-rose-500/30 text-[11px]">
                      {item.risk_score}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-14 h-1.5 rounded-full bg-[#0B1528] overflow-hidden">
                        <div
                          className="h-full bg-[#0D94FB] rounded-full"
                          style={{ width: `${Math.round((item.recovery_probability || 0.5) * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono text-[#879BBB] text-[11px]">
                        {Math.round((item.recovery_probability || 0.5) * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/recovery-agent?caseId=${item.id}`);
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0D94FB]/15 hover:bg-[#0D94FB]/25 text-[#0D94FB] border border-[#0D94FB]/30 text-xs font-semibold transition-colors"
                    >
                      <Zap className="w-3 h-3" />
                      <span>Run Agent</span>
                    </button>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && !loading && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-[#879BBB]">
                    No matching revenue risk cases found.
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
