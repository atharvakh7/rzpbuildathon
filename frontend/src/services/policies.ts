import { fetchApi } from './api';
import { AgentPermissions, PolicyConfigItem } from '../types';

export async function getPolicies(): Promise<{ policies: PolicyConfigItem[] }> {
  return fetchApi<{ policies: PolicyConfigItem[] }>('/api/policies');
}

export async function updatePolicies(policies: PolicyConfigItem[]): Promise<{ policies: PolicyConfigItem[] }> {
  return fetchApi<{ policies: PolicyConfigItem[] }>('/api/policies', {
    method: 'PUT',
    body: JSON.stringify({ policies }),
  });
}

export async function getAgentPermissions(): Promise<AgentPermissions> {
  return fetchApi<AgentPermissions>('/api/policies/permissions');
}
