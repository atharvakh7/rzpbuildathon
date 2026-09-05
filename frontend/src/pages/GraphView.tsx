import React, { useEffect, useState } from 'react';
import { Network, Search, User, CreditCard, AlertCircle, FileText, Handshake, RefreshCw, ShieldAlert, ChevronRight } from 'lucide-react';
import { getCustomerGraph } from '../services/graph';
import { getRevenueRiskQueue } from '../services/recovery';
import { GraphData, RevenueRiskItem } from '../types';
import { Currency } from '../components/Currency';

export const GraphView: React.FC = () => {
  const [candidates, setCandidates] = useState<RevenueRiskItem[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    getRevenueRiskQueue(undefined, undefined, 20).then((items) => {
      setCandidates(items);
      if (items.length > 0) {
        setSelectedCustomerId(items[0].customer_id);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedCustomerId) {
      loadGraph(selectedCustomerId);
    }
  }, [selectedCustomerId]);

  const loadGraph = async (cId: number) => {
    try {
      setLoading(true);
      const data = await getCustomerGraph(cId);
      setGraphData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const centerCustomer = graphData?.nodes.find((n) => n.type === 'customer');
  const connectedNodes = graphData?.nodes.filter((n) => n.type !== 'customer') || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Network className="w-6 h-6 text-[#0D94FB]" />
              <span>Entity Relationship Graph</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Risk Network
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Dynamic relational topology linking Customer profile &bull; Failure Events &bull; Payment Instruments &bull; Overdue Invoices &bull; Commitments.
          </p>
        </div>

        {/* Customer Selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-[#879BBB]">Target Account:</span>
          <select
            value={selectedCustomerId || ''}
            onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
            className="px-3 py-2 rounded-md bg-[#0B1528] border border-[#1E3256] text-xs text-slate-200 font-mono focus:outline-none focus:border-[#0D94FB]"
          >
            {candidates.map((c) => (
              <option key={c.id} value={c.customer_id}>
                {c.customer_name} (Cust #{c.customer_id} • ₹{c.amount.toLocaleString('en-IN')})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Interactive Node Graph Canvas */}
      <div className="p-8 rounded-lg bg-[#072654]/30 border border-[#1E3256] min-h-[500px] flex flex-col justify-center items-center relative overflow-hidden shadow-2xl backdrop-blur-sm">
        {/* Background Grid Accent */}
        <div className="absolute inset-0 bg-[radial-gradient(#1E3256_1px,transparent_1px)] [background-size:20px_20px] opacity-40 pointer-events-none" />

        {loading ? (
          <div className="flex items-center gap-3 text-[#879BBB] z-10">
            <RefreshCw className="w-5 h-5 animate-spin text-[#0D94FB]" />
            <span>Traversing relational database topology...</span>
          </div>
        ) : (
          <div className="w-full max-w-4xl z-10 flex flex-col items-center gap-10">
            {/* Center Node: Customer Profile */}
            {centerCustomer && (
              <div className="relative p-6 rounded-lg bg-gradient-to-br from-[#072654] via-[#111D33] to-[#111D33] border-2 border-[#0D94FB] shadow-xl shadow-[#0D94FB]/10 text-center max-w-sm w-full">
                <div className="w-12 h-12 rounded-full bg-[#0D94FB]/20 border border-[#0D94FB] text-[#0D94FB] flex items-center justify-center mx-auto mb-3 shadow-md shadow-[#0D94FB]/30">
                  <User className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-white tracking-tight">{centerCustomer.label}</h3>
                <span className="text-[10px] font-mono text-[#0D94FB] uppercase tracking-wider block mt-0.5 font-semibold">
                  ACCOUNT #{centerCustomer.id}
                </span>

                <div className="mt-4 pt-3 border-t border-[#1E3256] grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="text-left">
                    <span className="text-[10px] text-[#879BBB] uppercase block">Lifetime Value</span>
                    <span className="text-white font-bold">
                      <Currency amount={centerCustomer.data?.ltv || 0} />
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-[#879BBB] uppercase block">Settled Volume</span>
                    <span className="text-emerald-400 font-bold">
                      {centerCustomer.data?.previous_payments || 0} Paid
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Connected Child Nodes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 w-full">
              {connectedNodes.map((node) => {
                let icon = <AlertCircle className="w-4 h-4 text-rose-400" />;
                let border = 'border-rose-500/40';
                let tag = 'Risk Event';

                if (node.type === 'case') {
                  icon = <AlertCircle className="w-4 h-4 text-amber-400" />;
                  border = 'border-amber-500/40';
                  tag = 'Recovery Case';
                } else if (node.type === 'invoice') {
                  icon = <FileText className="w-4 h-4 text-blue-400" />;
                  border = 'border-blue-500/40';
                  tag = 'Receivable Invoice';
                } else if (node.type === 'promise') {
                  icon = <Handshake className="w-4 h-4 text-purple-400" />;
                  border = 'border-purple-500/40';
                  tag = 'Promise Commitment';
                } else if (node.type === 'payment_event') {
                  icon = <CreditCard className="w-4 h-4 text-rose-400" />;
                  border = 'border-rose-500/40';
                  tag = 'Declined Instrument';
                }

                return (
                  <div
                    key={node.id}
                    className={`p-4 rounded-lg bg-[#111D33] border ${border} shadow-md space-y-2.5 hover:border-[#0D94FB] transition-colors`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {icon}
                        <span className="text-[10px] font-bold uppercase text-[#879BBB] tracking-wider">
                          {tag}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-[#879BBB]">#{node.id}</span>
                    </div>

                    <h4 className="text-xs font-bold text-white tracking-tight">{node.label}</h4>

                    {node.data?.amount && (
                      <div className="font-mono text-xs text-emerald-400 font-bold">
                        <Currency amount={node.data.amount} />
                      </div>
                    )}
                    {node.data?.reason && (
                      <p className="text-[11px] text-[#879BBB]">
                        Reason: <span className="text-slate-200 font-mono">{node.data.reason}</span>
                      </p>
                    )}
                    {node.data?.status && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-[#0B1528] border border-[#1E3256] text-slate-300 font-mono inline-block">
                        Status: {node.data.status}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
