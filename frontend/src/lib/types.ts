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
  source_type: "review" | "crawler_artifact" | "agent_step";
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
