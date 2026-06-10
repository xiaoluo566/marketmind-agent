export type TaskStatus =
  | "received"
  | "queued"
  | "running"
  | "crawling"
  | "reasoning"
  | "retrieving"
  | "reporting"
  | "waiting_retry"
  | "completed"
  | "failed"
  | "cancelled";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type Task = {
  task_id: string;
  title: string;
  target: string;
  mode: string;
  status: TaskStatus;
  priority: "low" | "normal" | "high";
  source_type?: "demo_dataset" | "manual_upload" | "public_url";
  created_at: string;
  updated_at?: string;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
  trace_id: string;
  queue_task_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  report_id?: string;
};

export type TaskEvent = {
  event_id: string;
  task_id: string;
  module: "api" | "worker" | "crawler" | "agent" | "rag" | "report";
  event_type: string;
  status: TaskStatus;
  message: string;
  created_at: string;
  trace_id?: string | null;
  payload?: Record<string, unknown>;
};

export type AgentStep = {
  step_id: string;
  agent_run_id: string;
  task_id: string;
  step_index: number;
  step_type: "thought" | "action" | "observation" | "self_check";
  tool_name?: string;
  status: "pending" | "running" | "success" | "failed" | "skipped";
  duration_ms?: number;
  input_summary?: string;
  observation_summary?: string;
  error_code?: string;
};

export type Evidence = {
  evidence_id: string;
  source_type: "review" | "review_chunk" | "crawler_artifact" | "artifact" | "agent_step" | "missing";
  source_url: string;
  similarity: number;
  rating?: number;
  content: string;
  task_id: string;
  metadata: Record<string, string>;
};

export type ReportSection = {
  title: string;
  body: string;
  evidence_ids: string[];
};

export type Report = {
  report_id: string;
  task_id: string;
  title: string;
  summary: string;
  risk_level: RiskLevel;
  risk_score: number;
  evidence_count: number;
  created_at: string;
  sections: ReportSection[];
};

export type SystemService = {
  name: string;
  status: "healthy" | "mock" | "delayed" | "offline";
  detail: string;
};

export type LLMOpsSummary = {
  summary_version: string;
  generated_at: string;
  data_freshness: string;
  data_sources: string[];
  task_metrics: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    success_rate: number;
    failure_rate: number;
    average_duration_ms: number;
    data_source: string;
  };
  model_usage: {
    agent_run_count: number;
    model_call_count: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    reported_cost: number;
    cost_source: string;
    cost_confidence: string;
    data_source: string;
  };
  guardrail_metrics: {
    validation_error_count: number;
    self_heal_count: number;
    self_heal_success_rate: number;
    data_source: string;
  };
  recovery_metrics: {
    retry_requested_count: number;
    retry_requeued_count: number;
    recovery_resumed_count: number;
    retry_queue_unavailable_count: number;
    recovery_success_count: number;
    recovery_success_rate: number;
    data_source: string;
  };
  provider_metrics: {
    embedding_provider_calls: number;
    average_latency_ms: number;
    data_source: string;
    note: string;
  };
  warnings: string[];
};

export type TaskCreateInput = {
  target: string;
  mode: string;
  priority: "low" | "normal" | "high";
  source_type: "demo_dataset" | "manual_upload" | "public_url";
  options: Record<string, unknown>;
};

export type TaskAccepted = {
  task_id: string;
  status: string;
  trace_id: string;
  queue_task_id: string | null;
};

export type ReviewImportInput = {
  format: "csv" | "json";
  content: string;
  product_title: string;
  source_url?: string;
};

export type ReviewImportRowError = {
  row_number: number;
  field: string;
  message: string;
};

export type ReviewImportResult = {
  format: "csv" | "json";
  task_id: string;
  product_id: string;
  imported_count: number;
  duplicate_count: number;
  error_count: number;
  errors: ReviewImportRowError[];
  review_external_ids: string[];
};
