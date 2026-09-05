import React, { useState } from 'react';
import { Database, Play, RefreshCw, Zap, RotateCcw, CheckCircle2, TrendingUp, ShieldAlert, Cpu } from 'lucide-react';
import { generateSimulatedData, resetDemo, runBatchSimulation, getBatchStatus } from '../services/simulator';
import { BatchStatusResponse } from '../types';
import { Currency } from '../components/Currency';
import { StatusBadge } from '../components/StatusBadge';

export const DataSimulator: React.FC = () => {
  const [batchSize, setBatchSize] = useState<number>(100);
  const [paymentPct, setPaymentPct] = useState<number>(40);
  const [checkoutPct, setCheckoutPct] = useState<number>(30);
  const [receivablesPct, setReceivablesPct] = useState<number>(30);
  const [avgAmount, setAvgAmount] = useState<number>(5000);

  const [generating, setGenerating] = useState<boolean>(false);
  const [processing, setProcessing] = useState<boolean>(false);
  const [resetting, setResetting] = useState<boolean>(false);
  const [lastBatch, setLastBatch] = useState<BatchStatusResponse | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Generate synthetic dataset without running recovery loop
  const handleGenerateData = async () => {
    try {
      setGenerating(true);
      setMessage(null);
      const res = await generateSimulatedData({
        batch_size: batchSize,
        payment_pct: paymentPct,
        checkout_pct: checkoutPct,
        receivables_pct: receivablesPct,
        avg_transaction_value: avgAmount,
        failure_rate: 0.6,
      });
      setMessage(res.message);
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  // Run full batch simulation: generates records AND runs concurrent agent loop + baseline benchmark
  const handleRunBatch = async () => {
    try {
      setProcessing(true);
      setMessage(null);
      const initBatch = await runBatchSimulation({
        batch_size: batchSize,
        payment_pct: paymentPct,
        checkout_pct: checkoutPct,
        receivables_pct: receivablesPct,
        avg_transaction_value: avgAmount,
        failure_rate: 0.6,
      });
      setLastBatch(initBatch);

      // Poll until completed
      const pollInterval = setInterval(async () => {
        try {
          const status = await getBatchStatus(initBatch.id);
          setLastBatch(status);
          if (status.status === 'COMPLETED' || status.status === 'FAILED') {
            clearInterval(pollInterval);
            setProcessing(false);
            setMessage(
              `Batch #${status.id} completed! Processed ${status.events_processed} cases. Recovered ${status.recovery_rate}% of revenue at risk.`
            );
          }
        } catch {
          clearInterval(pollInterval);
          setProcessing(false);
        }
      }, 1500);
    } catch (err: any) {
      setMessage(`Batch execution failed: ${err.message}`);
      setProcessing(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset demo state? This will clear all records and re-seed 100 fresh realistic cases in database.')) {
      return;
    }
    try {
      setResetting(true);
      await resetDemo();
      setMessage('Demo database wiped and re-seeded with 100 cases!');
      setLastBatch(null);
    } catch (err: any) {
      setMessage(`Reset failed: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Cpu className="w-6 h-6 text-[#0D94FB]" />
              <span>Sandbox Recovery Batch Simulator</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Sandbox
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Generate dynamic transactions and trigger concurrent autonomous recovery agents with live baseline benchmarking.
          </p>
        </div>

        <button
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/40 text-xs font-semibold text-rose-300 transition-all disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
          <span>{resetting ? 'Resetting DB...' : 'Reset Demo Database'}</span>
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-[#111D33] border border-[#1E3256] text-xs text-emerald-400 font-mono flex items-center gap-2 shadow-md">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Simulator Controls Card */}
      <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-6 shadow-md">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider border-b border-[#1E3256] pb-3">
          Synthetic Event Parameters
        </h2>

        {/* Batch Size Selection */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Batch Volume (Direct DB Record Generation):
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[100, 500, 1000].map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => setBatchSize(size)}
                className={`py-3 rounded-md border font-mono text-sm font-bold transition-all ${
                  batchSize === size
                    ? 'bg-[#0D94FB]/15 border-[#0D94FB] text-[#0D94FB] shadow-md shadow-[#0D94FB]/20'
                    : 'bg-[#0B1528] border-[#1E3256] text-[#879BBB] hover:border-[#2A436E]'
                }`}
              >
                {size} Events
              </button>
            ))}
          </div>
        </div>

        {/* Category Distribution Sliders */}
        <div className="space-y-4 pt-2 border-t border-[#1E3256]">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
            Category Mix (%)
          </span>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256] space-y-2">
              <div className="flex justify-between">
                <span className="text-[#879BBB]">Payment Failures</span>
                <span className="text-emerald-400 font-bold">{paymentPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={paymentPct}
                onChange={(e) => setPaymentPct(Number(e.target.value))}
                className="w-full accent-[#0D94FB]"
              />
            </div>

            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256] space-y-2">
              <div className="flex justify-between">
                <span className="text-[#879BBB]">Checkout Abandonment</span>
                <span className="text-[#0D94FB] font-bold">{checkoutPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={checkoutPct}
                onChange={(e) => setCheckoutPct(Number(e.target.value))}
                className="w-full accent-[#0D94FB]"
              />
            </div>

            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256] space-y-2">
              <div className="flex justify-between">
                <span className="text-[#879BBB]">B2B Overdue Receivables</span>
                <span className="text-amber-400 font-bold">{receivablesPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={receivablesPct}
                onChange={(e) => setReceivablesPct(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
            </div>
          </div>
        </div>

        {/* Action Trigger Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-[#1E3256]">
          <button
            onClick={handleRunBatch}
            disabled={processing}
            className="flex-1 py-3.5 rounded-md bg-[#0D94FB] hover:bg-[#0B72C7] text-white font-bold text-sm flex items-center justify-center gap-2 shadow-md shadow-[#0D94FB]/25 transition-all disabled:opacity-40"
          >
            <Play className="w-4 h-4" />
            <span>
              {processing ? 'Running Concurrent Agent Batch...' : `Run Batch Recovery Loop (${batchSize} Events)`}
            </span>
          </button>

          <button
            onClick={handleGenerateData}
            disabled={generating || processing}
            className="px-6 py-3.5 rounded-md bg-[#0B1528] hover:bg-[#172744] text-slate-200 font-semibold text-xs border border-[#1E3256] transition-colors disabled:opacity-40"
          >
            {generating ? 'Generating in DB...' : 'Generate Synthetic Events Only'}
          </button>
        </div>
      </div>

      {/* Batch Live Execution & Results */}
      {lastBatch && (
        <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#1E3256] pb-3">
            <div>
              <span className="text-[10px] font-mono text-[#879BBB] uppercase">BATCH RUN #{lastBatch.id}</span>
              <h3 className="text-base font-bold text-white">Batch Recovery & Benchmark Results</h3>
            </div>
            <StatusBadge status={lastBatch.status} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256]">
              <span className="text-[10px] text-[#879BBB] uppercase block">Events Processed</span>
              <span className="text-xl font-bold text-white mt-1 block">
                {lastBatch.events_processed} / {lastBatch.batch_size}
              </span>
            </div>

            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256]">
              <span className="text-[10px] text-[#879BBB] uppercase block">Revenue at Risk</span>
              <span className="text-xl font-bold text-slate-200 mt-1 block">
                <Currency amount={lastBatch.revenue_at_risk} />
              </span>
            </div>

            <div className="p-4 rounded-md bg-emerald-950/30 border border-emerald-500/40">
              <span className="text-[10px] text-emerald-400 uppercase block font-bold">RecoverAI Recovered</span>
              <span className="text-xl font-bold text-emerald-300 mt-1 block">
                <Currency amount={lastBatch.revenue_recovered} />
              </span>
              <span className="text-[10px] text-emerald-400 block mt-1">
                Yield: {lastBatch.recovery_rate}%
              </span>
            </div>

            <div className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256]">
              <span className="text-[10px] text-[#879BBB] uppercase block font-bold">Baseline Recovered</span>
              <span className="text-xl font-bold text-slate-300 mt-1 block">
                <Currency amount={lastBatch.baseline_recovered} />
              </span>
              <span className="text-[10px] text-[#879BBB] block mt-1">
                Yield: {lastBatch.baseline_rate}%
              </span>
            </div>
          </div>

          {/* Incremental Recovery Delta */}
          <div className="p-5 rounded-lg bg-gradient-to-r from-[#072654] via-[#111D33] to-[#111D33] border border-[#0D94FB]/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#0D94FB]">
                Incremental Recovery vs. Generic Baseline:
              </span>
              <div className="text-2xl font-bold font-mono text-white mt-0.5">
                +<Currency amount={lastBatch.incremental_recovered} />
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs font-mono text-[#879BBB]">
              <div>
                <span className="text-[10px] block text-[#879BBB]">Actions Executed</span>
                <span className="text-white font-bold">{lastBatch.actions_executed}</span>
              </div>
              <div>
                <span className="text-[10px] block text-[#879BBB]">Escalations</span>
                <span className="text-purple-300 font-bold">{lastBatch.escalations}</span>
              </div>
              <div>
                <span className="text-[10px] block text-[#879BBB]">Policy Stops</span>
                <span className="text-slate-400 font-bold">{lastBatch.policy_stops}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
