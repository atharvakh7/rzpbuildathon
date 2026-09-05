import { fetchApi } from './api';
import {
  AnalyzeResponse,
  ExecuteResponse,
  RecoveryCaseDetail,
  RecoveryCaseListItem,
  RevenueRiskItem,
} from '../types';

export async function getRevenueRiskQueue(
  recoveryType?: string,
  status?: string,
  limit: number = 200,
  offset: number = 0
): Promise<RevenueRiskItem[]> {
  const params = new URLSearchParams();
  if (recoveryType && recoveryType !== 'ALL') params.append('recovery_type', recoveryType);
  if (status && status !== 'ALL') params.append('status', status);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<RevenueRiskItem[]>(`/api/revenue-risk?${params.toString()}`);
}

export async function getRecoveryCases(
  status?: string,
  recoveryType?: string,
  limit: number = 200,
  offset: number = 0
): Promise<RecoveryCaseListItem[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (recoveryType && recoveryType !== 'ALL') params.append('recovery_type', recoveryType);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<RecoveryCaseListItem[]>(`/api/recovery-cases?${params.toString()}`);
}

export async function getRecoveryCaseDetail(caseId: number): Promise<RecoveryCaseDetail> {
  return fetchApi<RecoveryCaseDetail>(`/api/recovery-cases/${caseId}`);
}

export async function analyzeRecoveryCase(caseId: number): Promise<AnalyzeResponse> {
  return fetchApi<AnalyzeResponse>(`/api/recovery-cases/${caseId}/analyze`, {
    method: 'POST',
  });
}

export async function executeRecoveryAction(
  caseId: number,
  actionType?: string,
  language: string = 'english'
): Promise<ExecuteResponse> {
  return fetchApi<ExecuteResponse>(`/api/recovery-cases/${caseId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ action_type: actionType, language }),
  });
}

export async function approveRecoveryCase(caseId: number): Promise<ExecuteResponse> {
  return fetchApi<ExecuteResponse>(`/api/recovery-cases/${caseId}/approve`, {
    method: 'POST',
  });
}

export async function stopRecoveryCase(caseId: number, reason: string): Promise<any> {
  return fetchApi(`/api/recovery-cases/${caseId}/stop`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}
