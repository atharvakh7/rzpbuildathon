import React, { useEffect, useState } from 'react';
import {
  CalendarClock,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Send,
  Building2,
  ShieldCheck,
  Zap,
  ArrowRight,
  ExternalLink,
  Check,
  X,
  Play,
  RotateCw,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  getMandateStats,
  listMandates,
  getMandateDetail,
  presentMandateNow,
  rescheduleMandate,
  MandateScheduleItem,
  MandateScheduleDetail,
  MandateStats,
} from '../services/mandates';
import { Currency } from '../components/Currency';

export const MandateSequencer: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<MandateStats | null>(null);
  const [mandates, setMandates] = useState<MandateScheduleItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<MandateScheduleDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [presenting, setPresenting] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, listData] = await Promise.all([
        getMandateStats(),
        listMandates(statusFilter, typeFilter),
      ]);
      setStats(statsData);
      setMandates(listData);

      // Preserve selection or pick first item
      if (listData.length > 0) {
        const targetId = selectedId && listData.some((m) => m.id === selectedId) ? selectedId : listData[0].id;
        setSelectedId(targetId);
        await loadDetail(targetId);
      } else {
        setSelectedId(null);
        setSelectedDetail(null);
      }
    } catch (err: any) {
      console.error('Failed to load mandate sequencer data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id: number) => {
    try {
      setDetailLoading(true);
      const detail = await getMandateDetail(id);
      setSelectedDetail(detail);
    } catch (err: any) {
      console.error('Failed to load mandate detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, typeFilter]);

  const handleSelectMandate = (id: number) => {
    setSelectedId(id);
    loadDetail(id);
  };

  const handlePresentNow = async (overrideSuccess?: boolean) => {
    if (!selectedId) return;
    try {
      setPresenting(true);
      setFeedbackMsg(null);
      const res = await presentMandateNow(selectedId, overrideSuccess);
      setFeedbackMsg({
        text: res.message,
        type: res.success ? 'success' : 'error',
      });
      // Refresh details and summary list
      await Promise.all([loadDetail(selectedId), getMandateStats().then(setStats)]);
      const refreshedList = await listMandates(statusFilter, typeFilter);
      setMandates(refreshedList);
    } catch (err: any) {
      setFeedbackMsg({
        text: `Presentation execution failed: ${err.message}`,
        type: 'error',
      });
    } finally {
      setPresenting(false);
    }
  };

  const handleReschedule = async (targetStage: number) => {
    if (!selectedId) return;
    try {
      setDetailLoading(true);
      await rescheduleMandate(selectedId, targetStage);
      setFeedbackMsg({
        text: `Mandate resequenced to Stage ${targetStage}. Next presentation scheduled.`,
        type: 'info',
      });
      await loadDetail(selectedId);
    } catch (err: any) {
      alert(`Reschedule failed: ${err.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const filteredMandates = mandates.filter((m) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      m.customer_name.toLowerCase().includes(term) ||
      m.umrn.toLowerCase().includes(term) ||
      m.bank_name.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <CalendarClock className="w-6 h-6 text-[#0D94FB]" />
              <span>Mandate Retry Sequencer</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30">
              Razorpay Subscriptions &bull; eNACH / UPI AutoPay
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Intelligent bank presentation scheduling aligned with clearing windows, salary liquidity cycles, and RBI pre-debit compliance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#0D94FB]' : ''}`} />
            <span>Refresh State</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-[#1E3256] bg-[#111D33]">
          <div className="text-[11px] font-semibold text-[#879BBB] uppercase tracking-wider">Total Mandates Monitored</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{stats?.total_mandates || 0}</div>
          <div className="text-[10px] text-[#879BBB] mt-1">Active recurring subscriptions</div>
        </div>

        <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-950/20">
          <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Mandates at Risk</div>
          <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">{stats?.at_risk_mandates || 0}</div>
          <div className="text-[10px] text-amber-400/80 mt-1">Under active re-presentation sequences</div>
        </div>

        <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-950/20">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Sequencer Recovered</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">
            <Currency amount={stats?.recovered_amount || 0} />
          </div>
          <div className="text-[10px] text-emerald-400/80 mt-1">
            {stats?.recovered_mandates || 0} mandates ({stats?.recovery_rate || 0}% recovery yield)
          </div>
        </div>

        <div className="p-4 rounded-lg border border-[#0D94FB]/30 bg-[#0D94FB]/10">
          <div className="text-[11px] font-semibold text-[#0D94FB] uppercase tracking-wider">Active Clearing Window</div>
          <div className="text-xs font-bold text-blue-200 mt-1 leading-snug">
            {stats?.next_clearing_window || 'Morning NACH Session (10:00 - 11:30 AM IST)'}
          </div>
          <div className="text-[10px] text-[#0D94FB]/80 mt-1">NPCI & Razorpay Settlement Switch</div>
        </div>
      </div>

      {/* Main Master-Detail Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Mandates List */}
        <div className="lg:col-span-4 rounded-lg border border-[#1E3256] bg-[#111D33] p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">Mandate Accounts</h2>
            <span className="text-[10px] font-mono text-[#879BBB]">{filteredMandates.length} total</span>
          </div>

          {/* Filters & Search */}
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Search by customer, bank, UMRN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-slate-200 placeholder-[#879BBB] focus:outline-none focus:border-[#0D94FB]"
            />
            <div className="grid grid-cols-2 gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-md bg-[#0B1528] border border-[#1E3256] text-[11px] text-slate-300 focus:outline-none focus:border-[#0D94FB]"
              >
                <option value="ALL">All Statuses</option>
                <option value="RESEQUENCED">Resequencing</option>
                <option value="RECOVERED">Recovered</option>
                <option value="FAILED">Failed</option>
              </select>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-md bg-[#0B1528] border border-[#1E3256] text-[11px] text-slate-300 focus:outline-none focus:border-[#0D94FB]"
              >
                <option value="ALL">All Types</option>
                <option value="UPI_AUTOPAY">UPI AutoPay</option>
                <option value="E_NACH">eNACH</option>
                <option value="CARD_SI">Card SI</option>
              </select>
            </div>
          </div>

          {/* Mandates Scroll List */}
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredMandates.length === 0 ? (
              <div className="p-6 text-center text-xs text-[#879BBB]">No matching mandate schedules found.</div>
            ) : (
              filteredMandates.map((m) => {
                const isSelected = selectedId === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => handleSelectMandate(m.id)}
                    className={`w-full text-left p-3.5 rounded-md border transition-all ${
                      isSelected
                        ? 'border-[#0D94FB] bg-[#0D94FB]/15 shadow-sm shadow-[#0D94FB]/20'
                        : 'border-[#1E3256] bg-[#0B1528] hover:bg-[#172744] hover:border-[#2A436E]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-xs font-semibold text-white">{m.customer_name}</div>
                        <div className="text-[10px] text-[#879BBB] font-mono mt-0.5 flex items-center gap-1">
                          <Building2 className="w-3 h-3 text-[#879BBB]" />
                          <span>{m.bank_name}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-bold text-emerald-400 font-mono">
                          <Currency amount={m.amount} />
                        </div>
                        <span
                          className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-md mt-1 inline-block ${
                            m.status === 'RECOVERED'
                              ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-500/40'
                              : m.status === 'RESEQUENCED'
                              ? 'bg-amber-950/80 text-amber-300 border border-amber-500/40'
                              : 'bg-red-950/80 text-red-400 border border-red-500/40'
                          }`}
                        >
                          {m.status}
                        </span>
                      </div>
                    </div>

                    <div className="mt-2.5 pt-2 border-t border-[#1E3256]/60 flex items-center justify-between text-[10px] text-[#879BBB]">
                      <span className="font-mono">{m.mandate_type}</span>
                      <span className="text-[#0D94FB] font-semibold">Stage {m.current_stage}/4</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Detailed Sequencer Visualizer */}
        <div className="lg:col-span-8 rounded-lg border border-[#1E3256] bg-[#111D33] p-6 space-y-6">
          {detailLoading && !selectedDetail ? (
            <div className="py-24 text-center">
              <RefreshCw className="w-8 h-8 text-[#0D94FB] animate-spin mx-auto mb-3" />
              <p className="text-xs text-[#879BBB]">Loading mandate retry schedule...</p>
            </div>
          ) : selectedDetail ? (
            <>
              {/* Detail Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-[#1E3256]">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white">{selectedDetail.customer_name}</h2>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                        selectedDetail.status === 'RECOVERED'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                          : 'bg-amber-950 text-amber-300 border border-amber-500/40'
                      }`}
                    >
                      {selectedDetail.status}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#0B1528] text-slate-300 border border-[#1E3256]">
                      {selectedDetail.mandate_type}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-xs text-[#879BBB]">
                    <span>
                      UMRN:{' '}
                      <strong className="text-slate-200 font-mono font-medium">{selectedDetail.umrn}</strong>
                    </span>
                    <span>&bull;</span>
                    <span>
                      Bank: <strong className="text-slate-200">{selectedDetail.bank_name}</strong>
                    </span>
                    <span>&bull;</span>
                    <span>
                      Frequency: <strong className="text-slate-200">{selectedDetail.frequency}</strong>
                    </span>
                  </div>
                </div>

                <div className="text-left sm:text-right">
                  <div className="text-[10px] text-[#879BBB] uppercase tracking-wider">Debit Amount</div>
                  <div className="text-xl font-bold text-emerald-400 font-mono">
                    <Currency amount={selectedDetail.amount} />
                  </div>
                  <div className="text-[10px] text-[#879BBB]">
                    Max Cap: <Currency amount={selectedDetail.max_amount} />
                  </div>
                </div>
              </div>

              {/* Compliance & RBI Advisory Banner */}
              <div className="p-3.5 rounded-md border border-[#0D94FB]/30 bg-[#0D94FB]/10 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-5 h-5 text-[#0D94FB] shrink-0" />
                  <div>
                    <span className="font-semibold text-blue-200">RBI e-Mandate Circular & Pre-Debit Advisory</span>
                    <p className="text-[11px] text-[#879BBB]">
                      Pre-debit notification requirement satisfied via Razorpay e-Mandate Gateway.
                    </p>
                  </div>
                </div>
                <div className="px-2.5 py-1 rounded-md bg-[#0D94FB]/20 text-[#0D94FB] text-[10px] font-bold uppercase tracking-wider border border-[#0D94FB]/40">
                  Razorpay Verified
                </div>
              </div>

              {/* Feedback Message */}
              {feedbackMsg && (
                <div
                  className={`p-3 rounded-md text-xs border flex items-center gap-2 ${
                    feedbackMsg.type === 'success'
                      ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                      : feedbackMsg.type === 'error'
                      ? 'bg-red-950/80 border-red-500/50 text-red-300'
                      : 'bg-[#0D94FB]/20 border-[#0D94FB]/50 text-blue-200'
                  }`}
                >
                  {feedbackMsg.type === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  )}
                  <span>{feedbackMsg.text}</span>
                </div>
              )}

              {/* Multi-Stage Sequencer Timeline */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#0D94FB]" />
                    <span>Intelligent Retry Sequence Timeline</span>
                  </h3>
                  <span className="text-[11px] text-[#879BBB] font-mono">
                    Current Stage: <strong className="text-[#0D94FB]">Stage {selectedDetail.current_stage}</strong>
                  </span>
                </div>

                <div className="relative pl-6 space-y-6 before:absolute before:left-[11px] before:top-3 before:bottom-3 before:w-0.5 before:bg-[#1E3256]">
                  {selectedDetail.sequences?.map((seq) => {
                    const isCurrent = seq.stage === selectedDetail.current_stage && selectedDetail.status !== 'RECOVERED';
                    const isCompleted = seq.status === 'COMPLETED';
                    const isSuccess = seq.result === 'SUCCESS';

                    return (
                      <div key={seq.stage} className="relative group">
                        {/* Node icon */}
                        <div
                          className={`absolute -left-6 top-1.5 w-6 h-6 rounded-full flex items-center justify-center border text-[10px] font-bold transition-all ${
                            isSuccess
                              ? 'bg-emerald-500 border-emerald-400 text-black shadow-lg shadow-emerald-500/30'
                              : isCompleted
                              ? 'bg-red-950 border-red-500/50 text-red-300'
                              : isCurrent
                              ? 'bg-[#0D94FB] border-blue-300 text-white animate-pulse shadow-lg shadow-[#0D94FB]/40'
                              : 'bg-[#0B1528] border-[#1E3256] text-[#879BBB]'
                          }`}
                        >
                          {isSuccess ? <Check className="w-3.5 h-3.5" /> : seq.stage}
                        </div>

                        {/* Card Content */}
                        <div
                          className={`ml-3 p-4 rounded-md border transition-all ${
                            isCurrent
                              ? 'border-[#0D94FB]/60 bg-[#0D94FB]/10 shadow-sm'
                              : isSuccess
                              ? 'border-emerald-500/40 bg-emerald-950/10'
                              : 'border-[#1E3256] bg-[#0B1528]'
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-white">{seq.title}</span>
                              <span
                                className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-md ${
                                  isSuccess
                                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30'
                                    : isCurrent
                                    ? 'bg-[#0D94FB]/20 text-[#0D94FB] border border-[#0D94FB]/40'
                                    : isCompleted
                                    ? 'bg-[#172744] text-[#879BBB]'
                                    : 'bg-[#0B1528] text-[#879BBB]'
                                }`}
                              >
                                {isSuccess ? 'CLEARED' : seq.status}
                              </span>
                            </div>

                            <div className="text-xs font-mono text-[#879BBB] flex items-center gap-1.5">
                              <span>Liquidity Probability:</span>
                              <span className="font-bold text-emerald-400">
                                {Math.round(seq.liquidity_probability * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                            <div className="p-2 rounded-md bg-[#111D33] border border-[#1E3256]">
                              <span className="text-[10px] uppercase text-[#879BBB] block">Clearing Window</span>
                              <span className="text-slate-200 font-medium">{seq.clearing_window}</span>
                            </div>
                            <div className="p-2 rounded-md bg-[#111D33] border border-[#1E3256]">
                              <span className="text-[10px] uppercase text-[#879BBB] block">Channel / Mechanism</span>
                              <span className="text-slate-200 font-medium">{seq.channel}</span>
                            </div>
                          </div>

                          {seq.notes && (
                            <p className="text-[11px] text-[#879BBB] mt-2 italic bg-[#111D33]/60 p-2 rounded-md border border-[#1E3256]">
                              &ldquo;{seq.notes}&rdquo;
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Execution Actions Bar */}
              <div className="pt-4 border-t border-[#1E3256] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePresentNow()}
                    disabled={presenting || selectedDetail.status === 'RECOVERED'}
                    className="flex items-center gap-2 px-4 py-2 rounded-md bg-[#0D94FB] hover:bg-[#0B72C7] text-white text-xs font-semibold shadow-md shadow-[#0D94FB]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className={`w-3.5 h-3.5 ${presenting ? 'animate-spin' : ''}`} />
                    <span>{presenting ? 'Presenting via Razorpay Switch...' : 'Trigger Presentation (Razorpay Switch)'}</span>
                  </button>

                  {/* Simulator Toggles for Evaluation/Testing */}
                  <div className="flex items-center rounded-md border border-[#1E3256] bg-[#0B1528] p-0.5">
                    <button
                      onClick={() => handlePresentNow(true)}
                      disabled={presenting || selectedDetail.status === 'RECOVERED'}
                      title="Simulate successful bank clearance"
                      className="px-2.5 py-1.5 text-[10px] font-semibold text-emerald-400 hover:bg-emerald-950/60 rounded-md disabled:opacity-40"
                    >
                      Force Success
                    </button>
                    <button
                      onClick={() => handlePresentNow(false)}
                      disabled={presenting || selectedDetail.status === 'RECOVERED'}
                      title="Simulate decline and advance to next stage"
                      className="px-2.5 py-1.5 text-[10px] font-semibold text-rose-400 hover:bg-rose-950/60 rounded-md disabled:opacity-40"
                    >
                      Force Fail
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {selectedDetail.case_id && (
                    <button
                      onClick={() => navigate(`/recovery-agent?caseId=${selectedDetail.case_id}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#111D33] hover:bg-[#172744] border border-[#1E3256] text-xs font-medium text-slate-200 transition-colors"
                    >
                      <span>View Case #{selectedDetail.case_id}</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="py-20 text-center text-xs text-[#879BBB]">Select a mandate account to view sequence.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MandateSequencer;
