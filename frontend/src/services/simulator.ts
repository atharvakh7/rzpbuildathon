import { fetchApi } from './api';
import { BatchStatusResponse } from '../types';

export interface SimulatorGenerateParams {
  batch_size: number;
  payment_pct: number;
  checkout_pct: number;
  receivables_pct: number;
  avg_transaction_value: number;
  failure_rate: number;
}

export async function generateSimulatedData(params: SimulatorGenerateParams): Promise<any> {
  return fetchApi('/api/simulator/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function resetDemo(): Promise<any> {
  return fetchApi('/api/simulator/reset', {
    method: 'POST',
  });
}

export async function runBatchSimulation(params: SimulatorGenerateParams): Promise<BatchStatusResponse> {
  return fetchApi<BatchStatusResponse>('/api/batch/run', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getBatchStatus(batchId: number): Promise<BatchStatusResponse> {
  return fetchApi<BatchStatusResponse>(`/api/batch/${batchId}`);
}
