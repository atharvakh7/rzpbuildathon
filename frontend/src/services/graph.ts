import { fetchApi } from './api';
import { GraphData } from '../types';

export async function getCustomerGraph(customerId: number): Promise<GraphData> {
  return fetchApi<GraphData>(`/api/graph/customer/${customerId}`);
}
