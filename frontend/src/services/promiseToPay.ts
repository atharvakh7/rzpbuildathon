import { fetchApi } from './api';
import { PromiseToPayItem } from '../types';

export async function getPromiseToPayList(status?: string): Promise<PromiseToPayItem[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  return fetchApi<PromiseToPayItem[]>(`/api/promise-to-pay?${params.toString()}`);
}

export async function createPromiseToPay(data: {
  customer_id: number;
  invoice_id: number;
  case_id?: number;
  amount: number;
  promise_date: string;
}): Promise<PromiseToPayItem> {
  return fetchApi<PromiseToPayItem>('/api/promise-to-pay', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePromiseStatus(promiseId: number, status: string): Promise<PromiseToPayItem> {
  return fetchApi<PromiseToPayItem>(`/api/promise-to-pay/${promiseId}/status?new_status=${status}`, {
    method: 'PUT',
  });
}
