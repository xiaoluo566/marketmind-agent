import { agentSteps, evidence, llmopsSummary, reports, services, taskEvents, tasks } from "./mock-data";
import type {
  AgentStep,
  Evidence,
  LLMOpsSummary,
  Report,
  Task,
  TaskAccepted,
  TaskCreateInput,
  TaskEvent,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";
const mockRetriedTaskIds = new Set<string>();

export type ApiEnvelope<T> = {
  success: boolean;
  data: T | null;
  error: {
    code: string;
    message?: string;
    details?: Record<string, unknown>;
  } | null;
  message: string;
  trace_id: string;
};

type ApiClientErrorOptions = {
  code: string;
  status: number;
  traceId?: string;
  details?: Record<string, unknown>;
};

export class ApiClientError extends Error {
  code: string;
  status: number;
  traceId?: string;
  details?: Record<string, unknown>;

  constructor(message: string, options: ApiClientErrorOptions) {
    super(message);
    this.name = "ApiClientError";
    this.code = options.code;
    this.status = options.status;
    this.traceId = options.traceId;
    this.details = options.details;
  }
}

export function isRealApiEnabled() {
  return !USE_MOCKS;
}

export function getApiModeLabel() {
  return isRealApiEnabled() ? "真实 API" : "模拟模式";
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  const envelope = (await response.json()) as ApiEnvelope<T>;

  if (!response.ok || !envelope.success || envelope.error) {
    throw new ApiClientError(envelope.error?.message ?? envelope.message, {
      code: envelope.error?.code ?? "API_REQUEST_FAILED",
      status: response.status,
      traceId: envelope.trace_id,
      details: envelope.error?.details,
    });
  }

  if (envelope.data === null) {
    throw new ApiClientError("API response did not include data", {
      code: "EMPTY_RESPONSE_DATA",
      status: response.status,
      traceId: envelope.trace_id,
    });
  }

  return envelope.data;
}

async function safeRequest<T>(path: string, fallback: T): Promise<T> {
  try {
    return await request<T>(path);
  } catch {
    return fallback;
  }
}

export async function createTask(payload: TaskCreateInput) {
  if (USE_MOCKS) {
    return {
      task_id: tasks[0]?.task_id ?? "tsk_mock_created",
      status: "queued",
      trace_id: "trc_mock_created",
      queue_task_id: "queue_mock_created",
    };
  }
  return request<TaskAccepted>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function retryTask(taskId: string) {
  if (USE_MOCKS) {
    mockRetriedTaskIds.add(taskId);
    return {
      task_id: taskId,
      status: "queued",
      trace_id: `mock_retry_${taskId}`,
      queue_task_id: `mock_retry_${taskId}`,
    };
  }
  return request<TaskAccepted>(`/api/tasks/${taskId}/retry`, {
    method: "POST",
  });
}

export async function listTasks() {
  if (USE_MOCKS) {
    return tasks;
  }
  const payload = await request<BackendTaskList>("/api/tasks");
  return payload.items.map(mapBackendTask);
}

export async function getTask(taskId: string) {
  if (USE_MOCKS) {
    const task = tasks.find((item) => item.task_id === taskId) ?? tasks[0];
    return mockRetriedTaskIds.has(task.task_id) ? buildMockRetriedTask(task) : task;
  }
  const task = await request<BackendTaskStatus>(`/api/tasks/${taskId}`);
  return mapBackendTask(task);
}

export async function getTaskEvents(taskId: string) {
  if (USE_MOCKS) {
    const events = taskEvents.filter((event) => event.task_id === taskId);
    if (!mockRetriedTaskIds.has(taskId)) {
      return events;
    }
    const retryEvent: TaskEvent = {
      event_id: `evt_mock_retry_${taskId}`,
      task_id: taskId,
      module: "api",
      event_type: "task.retry_submitted",
      status: "queued",
      message: "重试任务已提交，任务已重新进入队列。",
      created_at: new Date().toISOString(),
      trace_id: `mock_retry_${taskId}`,
      payload: { queue_task_id: `mock_retry_${taskId}` },
    };
    return [
      ...events,
      retryEvent,
    ];
  }
  const payload = await request<BackendTaskEvents>(`/api/tasks/${taskId}/events`);
  return payload.events.map(mapBackendTaskEvent);
}

export async function getTaskSteps(taskId: string) {
  if (USE_MOCKS) {
    const runId = taskId.replace("tsk", "run");
    return agentSteps.filter((step) => step.agent_run_id === runId);
  }
  try {
    const payload = await request<BackendTaskSteps>(`/api/tasks/${taskId}/steps`);
    return payload.steps.map(mapBackendAgentStep);
  } catch {
    return [];
  }
}

export async function listReports() {
  if (USE_MOCKS) {
    return reports;
  }
  const payload = await request<BackendReportList>("/api/reports");
  return payload.items.map(mapBackendReport);
}

export async function getReport(reportId: string) {
  if (USE_MOCKS) {
    return reports.find((report) => report.report_id === reportId) ?? reports[0];
  }
  const report = await request<BackendReportDetail>(`/api/reports/${reportId}`);
  return mapBackendReportDetail(report);
}

export async function getReportEvidence(reportId: string) {
  if (USE_MOCKS) {
    const report = reports.find((item) => item.report_id === reportId);
    if (!report) {
      return evidence;
    }
    const evidenceIds = new Set(report.sections.flatMap((section) => section.evidence_ids));
    return evidence.filter((item) => evidenceIds.has(item.evidence_id));
  }
  const payload = await request<BackendReportEvidence>(`/api/reports/${reportId}/evidence`);
  return payload.sources.map((source) => mapBackendEvidenceSource(source, payload.task_id));
}

export function getReportMarkdownExportUrl(report: Report, reportEvidence: Evidence[]) {
  if (USE_MOCKS) {
    return buildDataUrl("text/markdown", buildMockReportMarkdown(report, reportEvidence));
  }
  return `${API_BASE_URL}/api/reports/${encodeURIComponent(report.report_id)}/export/markdown`;
}

export function getReportEvidencePackageUrl(report: Report, reportEvidence: Evidence[]) {
  if (USE_MOCKS) {
    return buildDataUrl(
      "application/json",
      JSON.stringify(buildMockEvidencePackage(report, reportEvidence), null, 2),
    );
  }
  return `${API_BASE_URL}/api/reports/${encodeURIComponent(report.report_id)}/evidence-package`;
}

export async function listEvidence() {
  if (USE_MOCKS) {
    return evidence;
  }
  return safeRequest<typeof evidence>("/api/evidence", evidence);
}

export async function listServices() {
  return services.map((service) =>
    service.name === "API"
      ? {
          ...service,
          status: isRealApiEnabled() ? "healthy" : service.status,
          detail: isRealApiEnabled() ? API_BASE_URL : service.detail,
        }
      : service,
  );
}

export async function getLLMOpsSummary() {
  if (USE_MOCKS) {
    return llmopsSummary;
  }
  return request<LLMOpsSummary>("/api/observability/llmops-summary");
}

type BackendTaskStatus = {
  task_id: string;
  status: string;
  trace_id: string;
  target: string;
  mode: string;
  priority: "low" | "normal" | "high";
  source_type: "demo_dataset" | "manual_upload" | "public_url";
  options: Record<string, unknown>;
  queue_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

type BackendTaskList = {
  items: BackendTaskStatus[];
  limit: number;
  offset: number;
  total: number;
};

type BackendTaskEvents = {
  task_id: string;
  events: BackendTaskEvent[];
};

type BackendTaskEvent = {
  event_id: string;
  task_id: string;
  status: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown>;
  trace_id: string | null;
  created_at: string;
};

type BackendTaskSteps = {
  task_id: string;
  steps: BackendAgentStep[];
};

type BackendAgentStep = {
  step_id: string;
  agent_run_id: string;
  task_id: string;
  step_index: number;
  step_type: AgentStep["step_type"];
  tool_name: string | null;
  status: AgentStep["status"];
  duration_ms: number | null;
  input_summary: string | null;
  observation_summary: string | null;
  error_code: string | null;
};

type BackendReportSummary = {
  report_id: string;
  task_id: string;
  task_status: string | null;
  title: string;
  summary: string;
  status: string;
  risk_level: string;
  risk_score: number;
  evidence_count: number;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

type BackendReportList = {
  items: BackendReportSummary[];
  limit: number;
  offset: number;
  total: number;
};

type BackendReportSection = {
  title: string;
  body: string;
  evidence_ids: string[];
};

type BackendReportDetail = BackendReportSummary & {
  sections: BackendReportSection[];
  content_markdown: string;
  evidence_refs: string[];
};

type BackendReportEvidence = {
  report_id: string;
  task_id: string;
  evidence_refs: string[];
  sources: BackendEvidenceSource[];
  missing_refs: string[];
};

type BackendEvidenceSource = {
  evidence_ref: string;
  source_type: string;
  source_id: string;
  task_id: string | null;
  available: boolean;
  title: string | null;
  content_preview: string | null;
  source_url: string | null;
  parent_refs: string[];
  missing_reason: string | null;
  metadata: Record<string, unknown>;
};

function mapBackendTask(task: BackendTaskStatus): Task {
  return {
    task_id: task.task_id,
    title: buildTaskTitle(task.target),
    target: task.target,
    mode: task.mode,
    status: normalizeTaskStatus(task.status),
    priority: task.priority,
    source_type: task.source_type,
    created_at: task.created_at,
    updated_at: task.updated_at,
    started_at: task.started_at ?? undefined,
    finished_at: task.finished_at ?? undefined,
    duration_ms: durationMs(task.started_at, task.finished_at),
    trace_id: task.trace_id,
    queue_task_id: task.queue_task_id,
    error_code: task.error_code,
    error_message: task.error_message,
  };
}

function mapBackendReport(report: BackendReportSummary): Report {
  return {
    report_id: report.report_id,
    task_id: report.task_id,
    title: report.title,
    summary: report.summary,
    risk_level: normalizeRiskLevel(report.risk_level),
    risk_score: report.risk_score,
    evidence_count: report.evidence_count,
    created_at: report.created_at,
    sections: [],
  };
}

function mapBackendReportDetail(report: BackendReportDetail): Report {
  return {
    ...mapBackendReport(report),
    sections: report.sections.map((section) => ({
      title: section.title,
      body: section.body,
      evidence_ids: section.evidence_ids,
    })),
  };
}

function mapBackendEvidenceSource(source: BackendEvidenceSource, taskId: string): Evidence {
  return {
    evidence_id: source.evidence_ref,
    source_type: normalizeEvidenceSourceType(source.source_type),
    source_url: source.source_url ?? source.evidence_ref,
    similarity: source.available ? 1 : 0,
    rating: numericMetadataValue(source.metadata.rating),
    content: source.content_preview ?? source.missing_reason ?? "证据来源不可用。",
    task_id: source.task_id ?? taskId,
    metadata: stringifyMetadata({
      ...source.metadata,
      available: source.available,
      missing_reason: source.missing_reason,
      source_id: source.source_id,
      parent_refs: source.parent_refs,
    }),
  };
}

function mapBackendAgentStep(step: BackendAgentStep): AgentStep {
  return {
    step_id: step.step_id,
    agent_run_id: step.agent_run_id,
    task_id: step.task_id,
    step_index: step.step_index,
    step_type: step.step_type,
    tool_name: step.tool_name ?? undefined,
    status: step.status,
    duration_ms: step.duration_ms ?? undefined,
    input_summary: step.input_summary ?? undefined,
    observation_summary: step.observation_summary ?? undefined,
    error_code: step.error_code ?? undefined,
  };
}

function normalizeRiskLevel(level: string): Report["risk_level"] {
  const supported: Report["risk_level"][] = ["low", "medium", "high", "critical"];
  return supported.includes(level as Report["risk_level"])
    ? (level as Report["risk_level"])
    : "medium";
}

function normalizeEvidenceSourceType(sourceType: string): Evidence["source_type"] {
  const supported: Evidence["source_type"][] = [
    "review",
    "review_chunk",
    "crawler_artifact",
    "artifact",
    "agent_step",
    "missing",
  ];
  if (supported.includes(sourceType as Evidence["source_type"])) {
    return sourceType as Evidence["source_type"];
  }
  if (sourceType === "artifact") {
    return "crawler_artifact";
  }
  return "missing";
}

function numericMetadataValue(value: unknown) {
  return typeof value === "number" ? value : undefined;
}

function stringifyMetadata(metadata: Record<string, unknown>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(metadata)
      .filter(([, value]) => value !== null && value !== undefined)
      .map(([key, value]) => [
        key,
        Array.isArray(value) || typeof value === "object" ? JSON.stringify(value) : String(value),
      ]),
  );
}

function mapBackendTaskEvent(event: BackendTaskEvent): TaskEvent {
  return {
    event_id: event.event_id,
    task_id: event.task_id,
    module: inferEventModule(event.event_type),
    event_type: event.event_type,
    status: normalizeTaskStatus(event.status),
    message: translateBackendTaskEventMessage(event),
    created_at: event.created_at,
    trace_id: event.trace_id,
    payload: event.payload,
  };
}

function translateBackendTaskEventMessage(event: BackendTaskEvent): string {
  const translations: Record<string, string> = {
    "task waiting retry": "任务正在等待重试。",
    "task requeued": "任务已重新进入队列。",
    "task recovery resumed": "任务恢复执行已开始。",
    "task retry queue unavailable": "重试队列不可用。",
  };
  return translations[event.message] ?? event.message;
}

function buildMockRetriedTask(task: Task): Task {
  return {
    ...task,
    status: "queued",
    queue_task_id: `mock_retry_${task.task_id}`,
    error_code: null,
    error_message: null,
    finished_at: undefined,
    duration_ms: undefined,
    updated_at: new Date().toISOString(),
  };
}

function buildTaskTitle(target: string) {
  if (target.startsWith("demo://")) {
    return target.replace("demo://", "Demo dataset: ");
  }
  try {
    const url = new URL(target);
    return url.hostname;
  } catch {
    return target.slice(0, 80);
  }
}

function normalizeTaskStatus(status: string): Task["status"] {
  const supported: Task["status"][] = [
    "received",
    "queued",
    "running",
    "crawling",
    "reasoning",
    "retrieving",
    "reporting",
    "waiting_retry",
    "completed",
    "failed",
    "cancelled",
  ];
  return supported.includes(status as Task["status"]) ? (status as Task["status"]) : "running";
}

function inferEventModule(eventType: string): TaskEvent["module"] {
  if (eventType.includes("recovery")) {
    return "worker";
  }
  if (eventType.includes("retry")) {
    return "api";
  }
  if (eventType.includes("crawler")) {
    return "crawler";
  }
  if (eventType.includes("agent")) {
    return "agent";
  }
  if (eventType.includes("rag")) {
    return "rag";
  }
  if (eventType.includes("report")) {
    return "report";
  }
  if (eventType.includes("worker")) {
    return "worker";
  }
  return "api";
}

function durationMs(startedAt?: string | null, finishedAt?: string | null) {
  if (!startedAt) {
    return undefined;
  }
  const start = new Date(startedAt).getTime();
  const end = finishedAt ? new Date(finishedAt).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) {
    return undefined;
  }
  return end - start;
}

function buildDataUrl(mediaType: "text/markdown" | "application/json", content: string) {
  return `data:${mediaType};charset=utf-8,${encodeURIComponent(content)}`;
}

function buildMockReportMarkdown(report: Report, reportEvidence: Evidence[]) {
  const sections = report.sections
    .map((section) =>
      [
        `## ${section.title}`,
        "",
        section.body,
        "",
        `证据引用：${section.evidence_ids.map((id) => `\`${id}\``).join(", ") || "证据不足"}`,
        "",
      ].join("\n"),
    )
    .join("\n");
  const evidenceLines = reportEvidence
    .map((item) =>
      [
        `### ${item.evidence_id}`,
        "",
        item.content,
        "",
        `- 来源：${item.source_url}`,
        `- 相似度：${Math.round(item.similarity * 100)}%`,
        item.rating ? `- 评分：${item.rating}/5` : null,
        "",
      ]
        .filter(Boolean)
        .join("\n"),
    )
    .join("\n");

  return [
    `# ${report.title}`,
    "",
    report.summary,
    "",
    `- report_id：\`${report.report_id}\``,
    `- task_id：\`${report.task_id}\``,
    `- 风险评分：\`${report.risk_score}\``,
    "",
    sections,
    "## 证据摘录",
    "",
    evidenceLines || "证据不足",
    "",
  ].join("\n");
}

function buildMockEvidencePackage(report: Report, reportEvidence: Evidence[]) {
  return {
    package_version: "evidence_package.v1",
    report_id: report.report_id,
    task_id: report.task_id,
    title: report.title,
    summary: report.summary,
    generated_at: new Date().toISOString(),
    evidence_refs: Array.from(
      new Set(report.sections.flatMap((section) => section.evidence_ids)),
    ),
    sources: reportEvidence.map((item) => ({
      evidence_ref: item.evidence_id,
      source_type: item.source_type,
      task_id: item.task_id,
      available: true,
      content_preview: item.content,
      source_url: item.source_url,
      similarity: item.similarity,
      rating: item.rating,
      metadata: item.metadata,
    })),
  };
}
