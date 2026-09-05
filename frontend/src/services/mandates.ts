import { fetchApi } from './api';

export interface MandateSequenceStage {
  stage: number;
  title: string;
  scheduled_time: string;
  clearing_window: string;
  liquidity_probability: number;
  channel: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'SCHEDULED' | 'SKIPPED';
  result?: 'SUCCESS' | 'FAILED' | 'PENDING';
  notes?: string;
}

export interface MandateScheduleItem {
  id: number;
  customer_id: number;
  customer_name: string;
  customer_phone?: string;
  case_id?: number;
  umrn: string;
  mandate_type: string;
  bank_name: string;
  amount: number;
  max_amount: number;
  frequency: string;
  status: string;
  current_stage: number;
  failure_reason: string;
  decline_code: string;
  pre_debit_notified: boolean;
  next_presentation_at?: string;
  created_at: string;
}

export interface MandateScheduleDetail extends MandateScheduleItem {
  sequences: MandateSequenceStage[];
  case_status?: string;
  case_amount_at_risk?: number;
}

export interface MandateStats {
  total_mandates: number;
  at_risk_mandates: number;
  recovered_mandates: number;
  recovered_amount: number;
  total_risk_amount: number;
  recovery_rate: number;
  next_clearing_window: string;
  active_clearing_bank: string;
}

export interface PresentMandateResponse {
  success: boolean;
  mandate_id: number;
  umrn: string;
  stage: number;
  action_taken: string;
  clearing_window: string;
  amount_recovered: number;
  new_status: string;
  message: string;
}

export async function getMandateStats(): Promise<MandateStats> {
  return fetchApi<MandateStats>('/api/mandates/stats');
}

export async function listMandates(
  status?: string,
  mandateType?: string
): Promise<MandateScheduleItem[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (mandateType && mandateType !== 'ALL') params.append('mandate_type', mandateType);
  const query = params.toString() ? `?${params.toString()}` : '';
  return fetchApi<MandateScheduleItem[]>(`/api/mandates${query}`);
}

export async function getMandateDetail(id: number): Promise<MandateScheduleDetail> {
  return fetchApi<MandateScheduleDetail>(`/api/mandates/${id}`);
}

export async function presentMandateNow(
  id: number,
  overrideSuccess?: boolean
): Promise<PresentMandateResponse> {
  return fetchApi<PresentMandateResponse>(`/api/mandates/${id}/present-now`, {
    method: 'POST',
    body: JSON.stringify({
      override_success: overrideSuccess !== undefined ? overrideSuccess : null,
    }),
  });
}

export async function rescheduleMandate(
  id: number,
  targetStage: number,
  clearingWindow?: string
): Promise<{ status: string; message: string }> {
  return fetchApi<{ status: string; message: string }>(`/api/mandates/${id}/reschedule`, {
    method: 'POST',
    body: JSON.stringify({
      target_stage: targetStage,
      clearing_window: clearingWindow || null,
    }),
  });
}
