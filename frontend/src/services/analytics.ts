import { fetchApi } from './api';
import { AnalyticsData } from '../types';

export async function getAnalyticsData(): Promise<AnalyticsData> {
  return fetchApi<AnalyticsData>('/api/analytics');
}
