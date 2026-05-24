import { agentSteps, evidence, reports, services, taskEvents, tasks } from "./mock-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  const envelope = await response.json();
  return envelope.data as T;
}

export async function listTasks() {
  if (USE_MOCKS) {
    return tasks;
  }
  return request<typeof tasks>("/api/tasks");
}

export async function getTask(taskId: string) {
  if (USE_MOCKS) {
    return tasks.find((task) => task.task_id === taskId) ?? tasks[0];
  }
  return request<(typeof tasks)[number]>(`/api/tasks/${taskId}`);
}

export async function getTaskEvents(taskId: string) {
  if (USE_MOCKS) {
    return taskEvents.filter((event) => event.task_id === taskId);
  }
  return request<typeof taskEvents>(`/api/tasks/${taskId}/events`);
}

export async function getTaskSteps(taskId: string) {
  if (USE_MOCKS) {
    const runId = taskId.replace("tsk", "run");
    return agentSteps.filter((step) => step.agent_run_id === runId);
  }
  return request<typeof agentSteps>(`/api/tasks/${taskId}/steps`);
}

export async function listReports() {
  if (USE_MOCKS) {
    return reports;
  }
  return request<typeof reports>("/api/reports");
}

export async function getReport(reportId: string) {
  if (USE_MOCKS) {
    return reports.find((report) => report.report_id === reportId) ?? reports[0];
  }
  return request<(typeof reports)[number]>(`/api/reports/${reportId}`);
}

export async function listEvidence() {
  if (USE_MOCKS) {
    return evidence;
  }
  return request<typeof evidence>("/api/evidence");
}

export async function listServices() {
  return services;
}

