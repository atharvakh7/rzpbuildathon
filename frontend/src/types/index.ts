export interface DashboardData {
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  active_cases: number;
  recovered_cases: number;
  escalated_cases: number;
  stopped_cases: number;
  total_cases: number;
  pending_cases: number;
}

export interface RevenueRiskItem {
  id: number;
  customer_id: number;
  customer_name: string;
  amount: number;
  currency: string;
  recovery_type: 'PAYMENT' | 'CHECKOUT' | 'RECEIVABLES';
  root_cause: string | null;
  risk_score: number;
  recovery_probability: number;
  recommended_action: string | null;
  status: string;
  created_at: string;
}

export interface RecoveryCaseListItem {
  id: number;
  customer_id: number;
  customer_name: string;
  amount_at_risk: number;
  currency: string;
  recovery_type: string;
  root_cause: string | null;
  confidence: number | null;
  status: string;
  attempt_count: number;
  amount_recovered: number;
  created_at: string;
}

export interface InterventionAnalysis {
  action: string;
  recovery_probability: number;
  intervention_cost: number;
  expected_recovery_value: number;
  incremental_recovery: number;
  baseline_probability: number;
  policy_status: 'ALLOWED' | 'DENIED' | 'REQUIRES_APPROVAL';
  policy_reason?: string;
}

export interface RecoveryActionItem {
  id: number;
  action_type: string;
  recovery_probability?: number;
  intervention_cost: number;
  expected_recovery_value: number;
  incremental_recovery: number;
  policy_status?: string;
  policy_reason?: string;
  execution_result?: string;
  amount_recovered: number;
  attempt_number: number;
  message_content?: string;
  message_language?: string;
  created_at: string;
}

export interface TimelineEntry {
  timestamp: string;
  event: string;
  detail?: string;
  status?: string;
}

export interface RecoveryCaseDetail {
  id: number;
  customer_id: number;
  customer_name: string;
  customer_email?: string;
  customer_phone?: string;
  customer_ltv: number;
  customer_tenure_months: number;
  customer_previous_payments: number;
  customer_previous_failures: number;
  customer_opt_out: boolean;
  customer_dispute_status: boolean;
  customer_hardship_status: boolean;
  amount_at_risk: number;
  currency: string;
  recovery_type: string;
  root_cause: string | null;
  confidence: number | null;
  evidence: string[];
  risk_score: number;
  recovery_probability: number;
  status: string;
  stop_reason?: string;
  attempt_count: number;
  amount_recovered: number;
  payment_method?: string;
  failure_reason?: string;
  days_overdue?: number;
  created_at: string;
  updated_at: string;
  actions: RecoveryActionItem[];
  timeline: TimelineEntry[];
}

export interface AnalyzeResponse {
  case_id: number;
  root_cause: string;
  confidence: number;
  evidence: string[];
  interventions: InterventionAnalysis[];
  recommended_action: string;
  agent_explanation: string;
  why_not_alternatives: Record<string, string>;
}

export interface ExecuteResponse {
  case_id: number;
  action_type: string;
  policy_result: string;
  policy_reason?: string;
  execution_result: string;
  amount_recovered: number;
  case_status: string;
  stop_reason?: string;
  message_content?: string;
  agent_explanation?: string;
}

export interface LedgerEntry {
  id: number;
  case_id: number;
  customer_id: number;
  customer_name?: string;
  recovery_type: string;
  amount_at_risk: number;
  root_cause?: string;
  confidence?: number;
  recommended_action?: string;
  selected_action?: string;
  recovery_probability?: number;
  expected_recovery_value?: number;
  policy_result?: string;
  policy_reason?: string;
  execution_result?: string;
  amount_recovered: number;
  status?: string;
  stop_reason?: string;
  agent_explanation?: string;
  created_at: string;
}

export interface PolicyConfigItem {
  key: string;
  value: string;
  description?: string;
}

export interface AgentPermissions {
  autonomous: string[];
  requires_approval: string[];
  never_allowed: string[];
}

export interface CategoryStat {
  category: string;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  cases: number;
}

export interface InterventionStat {
  action: string;
  count: number;
  success_count: number;
  success_rate: number;
  total_recovered: number;
  avg_recovered: number;
}

export interface AnalyticsData {
  total_revenue_at_risk: number;
  total_revenue_recovered: number;
  overall_recovery_rate: number;
  total_cases: number;
  by_category: CategoryStat[];
  by_intervention: InterventionStat[];
  baseline_recovered: number;
  baseline_rate: number;
  recoverai_recovered: number;
  recoverai_rate: number;
  incremental_recovered: number;
  escalation_rate: number;
  avg_recovery_amount: number;
  cost_per_recovery: number;
}

export interface PromiseToPayItem {
  id: number;
  customer_id: number;
  customer_name?: string;
  invoice_id: number;
  case_id?: number;
  amount: number;
  currency: string;
  promise_date: string;
  status: string;
  reminder_sent: boolean;
  created_at: string;
}

export interface BatchStatusResponse {
  id: number;
  batch_size: number;
  status: string;
  events_processed: number;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  actions_executed: number;
  successful_actions: number;
  escalations: number;
  policy_stops: number;
  baseline_recovered: number;
  baseline_rate: number;
  incremental_recovered: number;
  created_at: string;
  completed_at?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  data: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
