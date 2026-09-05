import React, { useEffect, useState } from 'react';
import { Sliders, Save, CheckCircle, RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react';
import { getPolicies, updatePolicies } from '../services/policies';
import { PolicyConfigItem } from '../types';

export const Policies: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyConfigItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const res = await getPolicies();
      setPolicies(res.policies);
    } catch (err: any) {
      setError(err.message || 'Failed to load policy configurations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleChange = (key: string, newValue: string) => {
    setPolicies((prev) =>
      prev.map((p) => (p.key === key ? { ...p, value: newValue } : p))
    );
    setSavedSuccess(false);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await updatePolicies(policies);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to save updated policies');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Sliders className="w-6 h-6 text-[#0D94FB]" />
              <span>Policy Guardrails Configuration</span>
            </h1>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 font-mono">
              Razorpay Rules
            </span>
          </div>
          <p className="text-xs text-[#879BBB] mt-1">
            Dynamic guardrails evaluated before any recovery intervention executes. Changes take immediate effect across all channels.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-[#0D94FB] hover:bg-[#0B72C7] text-white text-xs font-bold shadow-md shadow-[#0D94FB]/30 transition-all disabled:opacity-50"
        >
          {saving ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Updating Rules...</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>Save & Enforce Policies</span>
            </>
          )}
        </button>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-3 shadow-md shadow-emerald-950/40">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            Policies successfully updated in database! The autonomous recovery engine will enforce these updated boundaries immediately.
          </span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Rules Card */}
      <div className="p-6 rounded-lg bg-[#111D33] border border-[#1E3256] space-y-6 shadow-md">
        <div className="flex items-center gap-2 border-b border-[#1E3256] pb-4">
          <ShieldCheck className="w-4 h-4 text-[#0D94FB]" />
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">
            Deterministic Execution Limits
          </h2>
        </div>

        <div className="space-y-4">
          {policies.map((p) => (
            <div
              key={p.key}
              className="p-4 rounded-md bg-[#0B1528] border border-[#1E3256] flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-[#2A436E] transition-colors"
            >
              <div className="space-y-1">
                <span className="font-mono text-xs font-bold text-[#0D94FB]">{p.key}</span>
                <p className="text-xs text-[#879BBB]">{p.description}</p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <input
                  type="text"
                  value={p.value}
                  onChange={(e) => handleChange(p.key, e.target.value)}
                  className="w-32 px-3 py-2 rounded-md bg-[#111D33] border border-[#1E3256] text-right font-mono text-xs font-bold text-white focus:outline-none focus:border-[#0D94FB] transition-colors"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
