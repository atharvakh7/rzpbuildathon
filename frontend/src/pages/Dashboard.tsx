import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  AlertOctagon,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Zap,
  ArrowRight,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { getDashboardData } from '../services/dashboard';
import { getRevenueRiskQueue } from '../services/recovery';
import { DashboardData, RevenueRiskItem } from '../types';
import { MetricCard } from '../components/MetricCard';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
} from 'recharts';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [recentRisks, setRecentRisks] = useState<RevenueRiskItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      setLoading(true);
      const [dash, risks] = await Promise.all([
        getDashboardData(),
        getRevenueRiskQueue(undefined, undefined, 6),
      ]);
      setData(dash);
      setRecentRisks(risks);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <RefreshCw className="w-6 h-6 animate-spin text-emerald-400 mr-3" />
        <span>Loading live database metrics...</span>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-6 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5" />
          <span className="font-semibold">Backend Connection Error</span>
        </div>
        <p className="mt-2 text-sm text-rose-200">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 rounded-lg bg-rose-800/60 hover:bg-rose-700 text-xs font-semibold text-white"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // Dynamic chart data calculated directly from live DB metrics
  const performanceChartData = [
    { name: 'Active Risk', value: data?.revenue_at_risk || 0, fill: '#EF4444' },
    { name: 'Recovered', value: data?.revenue_recovered || 0, fill: '#10B981' },
  ];

  const caseDistribution = [
    { name: 'Active', count: data?.active_cases || 0 },
    { name: 'Recovered', count: data?.recovered_cases || 0 },
    { name: 'Escalated', count: data?.escalated_cases || 0 },
    { name: 'Stopped', count: data?.stopped_cases || 0 },
  ];

  return (
    <div className="space-y-8">
      {/* Top Banner with Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Command Center</span>
            <span className="text-xs px-2 py-0.5 rounded bg-[#0D94FB]/20 text-[#0D94FB] border border-[#0D94FB]/40 font-mono font-bold">
              RAZORPAY LIVE
            </span>
          </h1>
          <p className="text-xs text-[#879BBB] mt-1">
            Real-time agentic revenue recovery across Payments, Checkouts, and Overdue Receivables.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
            <span>Sync State</span>
          </button>
          <button
            onClick={() => navigate('/revenue-risk')}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-[#0D94FB] hover:bg-[#0B72C7] text-xs font-semibold text-white shadow-md shadow-[#0D94FB]/20 transition-all"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Process Revenue Risk</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Revenue at Risk"
          value={<Currency amount={data?.revenue_at_risk || 0} compact />}
          subtitle={`Across ${data?.active_cases || 0} active unresolved cases`}
          icon={AlertOctagon}
          trend={{ value: `${data?.active_cases || 0} active`, positive: false }}
        />

        <MetricCard
          title="Revenue Recovered"
          value={<Currency amount={data?.revenue_recovered || 0} compact />}
          subtitle={`Recovered from ${data?.recovered_cases || 0} closed cases`}
          icon={TrendingUp}
          highlight
          trend={{ value: `+₹${((data?.revenue_recovered || 0) / 1000).toFixed(1)}k`, positive: true }}
        />

        <MetricCard
          title="Recovery Yield"
          value={`${data?.recovery_rate || 0}%`}
          subtitle="Proportion of detected revenue recovered"
          icon={ShieldCheck}
          trend={{
            value: (data?.recovery_rate || 0) > 30 ? 'Strong Yield' : 'Optimizing',
            positive: (data?.recovery_rate || 0) > 30,
          }}
        />

        <MetricCard
          title="Autonomous Resolution"
          value={data?.recovered_cases || 0}
          subtitle={`${data?.escalated_cases || 0} escalated • ${data?.stopped_cases || 0} policy-stopped`}
          icon={CheckCircle2}
        />
      </div>

      {/* Visual Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recovery Balance Card */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Financial Exposure vs. Recovery</h2>
              <p className="text-xs text-[#879BBB]">Total captured from active database records</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              {data?.recovery_rate}% Recovered
            </span>
          </div>

          <div className="h-48 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={performanceChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3256" horizontal={false} />
                <XAxis
                  type="number"
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                  stroke="#879BBB"
                  fontSize={11}
                />
                <YAxis dataKey="name" type="category" stroke="#879BBB" fontSize={11} width={80} />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Amount']}
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E3256', borderRadius: '6px' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Case State Breakdown */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Workflow State Distribution</h2>
              <p className="text-xs text-[#879BBB]">Cases grouped by agent execution state</p>
            </div>
            <span className="text-xs font-mono text-[#879BBB]">{data?.total_cases || 0} Total</span>
          </div>

          <div className="h-48 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={caseDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3256" vertical={false} />
                <XAxis dataKey="name" stroke="#879BBB" fontSize={11} />
                <YAxis stroke="#879BBB" fontSize={11} />
                <Tooltip
                  formatter={(val: any) => [val, 'Cases']}
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E3256', borderRadius: '6px' }}
                />
                <Bar dataKey="count" fill="#0D94FB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bounded Autonomy Card */}
        <div className="p-6 rounded-lg bg-gradient-to-br from-[#111D33] to-[#0D2137] border border-[#1E3256] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0D94FB]">
                Blade Agentic Engine
              </span>
              <span className="w-2 h-2 rounded-full bg-[#0D94FB] animate-ping" />
            </div>
            <h2 className="text-base font-bold text-white">Expected Recovery Value (ERV)</h2>
            <p className="text-xs text-[#879BBB] mt-2 leading-relaxed">
              Interventions are dynamically chosen using Razorpay economic optimization:
            </p>
            <div className="mt-3 p-3 rounded-md bg-[#0B1528] border border-[#1E3256] font-mono text-xs text-[#0D94FB]">
              ERV = P(recovery) × Amount − Cost
            </div>
            <p className="text-xs text-slate-400 mt-3 leading-relaxed">
              Actions pass through deterministic Razorpay policy guardrails before automated execution.
            </p>
          </div>

          <div className="pt-4 border-t border-[#1E3256] flex items-center justify-between">
            <button
              onClick={() => navigate('/agent-permissions')}
              className="text-xs text-[#0D94FB] hover:text-blue-300 font-medium flex items-center gap-1.5"
            >
              <span>View Bounded Autonomy Matrix</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Active Revenue Risk Stream */}
      <div className="rounded-lg border border-[#1E3256] bg-[#111D33] overflow-hidden">
        <div className="p-5 border-b border-[#1E3256] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Highest Value Exposure at Risk</h2>
            <p className="text-xs text-[#879BBB]">Real-time queue prioritized by financial severity and recovery odds</p>
          </div>
          <button
            onClick={() => navigate('/revenue-risk')}
            className="text-xs text-[#0D94FB] hover:text-blue-300 font-medium flex items-center gap-1"
          >
            <span>View All Cases</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B1528] text-[#879BBB] font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-3">Case ID</th>
                <th className="px-6 py-3">Customer</th>
                <th className="px-6 py-3">Amount at Risk</th>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Root Cause</th>
                <th className="px-6 py-3">Recovery Odds</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3256]/60 font-medium">
              {recentRisks.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-[#172744]/60 transition-colors cursor-pointer"
                  onClick={() => navigate(`/recovery-agent?caseId=${item.id}`)}
                >
                  <td className="px-6 py-4 font-mono text-slate-300">#{item.id}</td>
                  <td className="px-6 py-4 text-white font-semibold">{item.customer_name}</td>
                  <td className="px-6 py-4 text-emerald-400 font-mono font-bold">
                    <Currency amount={item.amount} />
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[11px] px-2 py-0.5 rounded-md bg-[#0B1528] text-slate-300 border border-[#1E3256] font-mono">
                      {item.recovery_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {item.root_cause ? item.root_cause.replace(/_/g, ' ') : 'Pending Analysis'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-[#0B1528] overflow-hidden">
                        <div
                          className="h-full bg-[#0D94FB] rounded-full"
                          style={{ width: `${Math.round((item.recovery_probability || 0.5) * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono text-[#879BBB]">
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
                      className="px-3 py-1 rounded-md bg-[#0D94FB]/15 hover:bg-[#0D94FB]/25 text-[#0D94FB] border border-[#0D94FB]/30 text-xs font-semibold transition-colors"
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
              {recentRisks.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                    No active risk cases found. Generate cases via Data Simulator.
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
