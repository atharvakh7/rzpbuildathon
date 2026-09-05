import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { RevenueRisk } from './pages/RevenueRisk';
import { RecoveryAgent } from './pages/RecoveryAgent';
import { RecoveryCases } from './pages/RecoveryCases';
import { RecoveryLedger } from './pages/RecoveryLedger';
import { PromiseToPay } from './pages/PromiseToPay';
import { MandateSequencer } from './pages/MandateSequencer';
import { Analytics } from './pages/Analytics';
import { Policies } from './pages/Policies';
import { AgentPermissions } from './pages/AgentPermissions';
import { DataSimulator } from './pages/DataSimulator';
import { GraphView } from './pages/GraphView';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="revenue-risk" element={<RevenueRisk />} />
          <Route path="recovery-agent" element={<RecoveryAgent />} />
          <Route path="recovery-cases" element={<RecoveryCases />} />
          <Route path="ledger" element={<RecoveryLedger />} />
          <Route path="promise-to-pay" element={<PromiseToPay />} />
          <Route path="mandates" element={<MandateSequencer />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="policies" element={<Policies />} />
          <Route path="agent-permissions" element={<AgentPermissions />} />
          <Route path="simulator" element={<DataSimulator />} />
          <Route path="graph" element={<GraphView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
