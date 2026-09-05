import { fetchApi } from './api';
import { DashboardData } from '../types';

export async function getDashboardData(): Promise<DashboardData> {
  return fetchApi<DashboardData>('/api/dashboard');
}
