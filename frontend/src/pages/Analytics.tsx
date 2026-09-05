import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  RefreshCw,
  PieChart as PieIcon,
  Layers,
  Zap,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react';
import { getAnalyticsData } from '../services/analytics';
import { AnalyticsData } from '../types';
import { MetricCard } from '../components/MetricCard';
import { Currency } from '../components/Currency';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

export const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const res = await getAnalyticsData();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64 text-[#879BBB]">
        <RefreshCw className="w-6 h-6 animate-spin text-[#0D94FB] mr-3" />
        <span>Aggregating analytics from database...</span>
      </div>
    );
  }

  // Baseline vs RecoverAI A/B comparison data
  const comparisonData = [
    {
      metric: 'Revenue Recovered (INR)',
      Baseline: data?.baseline_recovered || 0,
      RecoverAI: data?.recoverai_recovered || 0,
    },
  ];

  const rateComparison = [
    {
      metric: 'Recovery Rate (%)',
      Baseline: data?.baseline_rate || 0,
      RecoverAI: data?.recoverai_rate || 0,
    },
  ];

  const categoryChartData = (data?.by_category || []).map((c) => ({
    name: c.category,
    Risk: c.revenue_at_risk,
    Recovered: c.revenue_recovered,
    Rate: c.recovery_rate,
  }));

  const interventionChartData = (data?.by_intervention || []).map((i) => ({
    name: i.action.replace(/_/g, ' '),
    count: i.count,
    success: i.success_count,
    rate: i.success_rate,
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-[#0D94FB]" />
              <span>Recovery Performance & Uplift Analytics</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Benchmark
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Deterministic side-by-side comparison of RecoverAI Agent vs. Standard Industry Baseline on live records.
          </p>
        </div>

        <button
          onClick={loadAnalytics}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
          <span>Recalculate</span>
        </button>
      </div>

      {/* Incremental Uplift Highlight Banner */}
      <div className="p-6 rounded-lg bg-gradient-to-r from-[#072654] via-[#111D33] to-[#111D33] border border-[#0D94FB]/40 shadow-lg shadow-[#0D94FB]/5 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-[#0D94FB]">
            Estimated Incremental Recovery
          </span>
          <div className="mt-1 flex items-baseline gap-3">
            <span className="text-3xl font-extrabold font-mono text-white">
              <Currency amount={data?.incremental_recovered || 0} />
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              +{Math.max(0, (data?.recoverai_rate || 0) - (data?.baseline_rate || 0)).toFixed(1)}% Absolute Uplift
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Additional cash recovered by RecoverAI over generic single-retry baseline on the exact same records.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="p-3 rounded-md bg-[#0B1528] border border-[#1E3256]">
            <span className="text-[#879BBB] block text-[10px] uppercase">Avg Recovery Amount</span>
            <span className="text-white font-bold">
              <Currency amount={data?.avg_recovery_amount || 0} />
            </span>
          </div>
          <div className="p-3 rounded-md bg-[#0B1528] border border-[#1E3256]">
            <span className="text-[#879BBB] block text-[10px] uppercase">Cost Per Recovery</span>
            <span className="text-emerald-400 font-bold">
              <Currency amount={data?.cost_per_recovery || 0} />
            </span>
          </div>
          <div className="p-3 rounded-md bg-[#0B1528] border border-[#1E3256]">
            <span className="text-[#879BBB] block text-[10px] uppercase">Escalation Rate</span>
            <span className="text-purple-300 font-bold">{data?.escalation_rate || 0}%</span>
          </div>
        </div>
      </div>

      {/* RecoverAI vs Baseline Side-by-Side Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Recovered Comparison */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-white">Baseline vs. RecoverAI Cash Recovered</h2>
              <p className="text-xs text-[#879BBB]">Total recovered on processed cases</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              +<Currency amount={data?.incremental_recovered || 0} /> Uplift
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3256" />
                <XAxis dataKey="metric" stroke="#879BBB" fontSize={11} />
                <YAxis
                  stroke="#879BBB"
                  fontSize={11}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Amount']}
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E3256', borderRadius: '6px' }}
                />
                <Legend />
                <Bar dataKey="Baseline" fill="#475569" radius={[4, 4, 0, 0]} />
                <Bar dataKey="RecoverAI" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recovery Rate Comparison */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-white">Recovery Yield Benchmark (%)</h2>
              <p className="text-xs text-[#879BBB]">Percentage of revenue at risk successfully settled</p>
            </div>
            <span className="text-xs font-mono text-[#0D94FB] font-bold">
              {data?.recoverai_rate}% vs {data?.baseline_rate}%
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rateComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3256" />
                <XAxis dataKey="metric" stroke="#879BBB" fontSize={11} />
                <YAxis stroke="#879BBB" fontSize={11} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Rate']}
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E3256', borderRadius: '6px' }}
                />
                <Legend />
                <Bar dataKey="Baseline" fill="#475569" radius={[4, 4, 0, 0]} />
                <Bar dataKey="RecoverAI" fill="#0D94FB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Category Performance Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-4">
          <h2 className="text-sm font-bold text-white">Performance by Loss Category</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3256" />
                <XAxis dataKey="name" stroke="#879BBB" fontSize={11} />
                <YAxis
                  stroke="#879BBB"
                  fontSize={11}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Amount']}
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E3256', borderRadius: '6px' }}
                />
                <Legend />
                <Bar dataKey="Risk" fill="#EF4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Recovered" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Intervention Success Table */}
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-4">
          <h2 className="text-sm font-bold text-white">Yield by Intervention Strategy</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase font-bold text-[#879BBB] border-b border-[#1E3256]">
                <tr>
                  <th className="py-2.5">Strategy</th>
                  <th className="py-2.5">Executions</th>
                  <th className="py-2.5">Success Rate</th>
                  <th className="py-2.5 text-right">Cash Recovered</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E3256]/60 font-medium">
                {(data?.by_intervention || []).map((row) => (
                  <tr key={row.action} className="hover:bg-[#172744]/40 transition-colors">
                    <td className="py-3 text-white font-semibold">{row.action.replace(/_/g, ' ')}</td>
                    <td className="py-3 font-mono text-[#879BBB]">{row.count}</td>
                    <td className="py-3">
                      <span className="font-mono text-emerald-400 font-semibold">{row.success_rate}%</span>
                    </td>
                    <td className="py-3 text-right font-mono font-bold text-emerald-400">
                      <Currency amount={row.total_recovered} />
                    </td>
                  </tr>
                ))}
                {(data?.by_intervention || []).length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-[#879BBB]">
                      No actions executed yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
