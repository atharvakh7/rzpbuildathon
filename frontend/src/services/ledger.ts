import { fetchApi } from './api';
import { LedgerEntry } from '../types';

export async function getLedgerEntries(
  caseId?: number,
  limit: number = 200,
  offset: number = 0
): Promise<LedgerEntry[]> {
  const params = new URLSearchParams();
  if (caseId) params.append('case_id', caseId.toString());
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<LedgerEntry[]>(`/api/ledger?${params.toString()}`);
}

export async function getLedgerEntry(entryId: number): Promise<LedgerEntry> {
  return fetchApi<LedgerEntry>(`/api/ledger/${entryId}`);
}
