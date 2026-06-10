"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AgentStepsTable } from "@/components/agent-steps-table";
import { StatusBadge } from "@/components/status-badge";
import { TaskTimeline } from "@/components/task-timeline";
import { ApiClientError, getTask, getTaskEvents, getTaskSteps, retryTask } from "@/lib/api";
import type { AgentStep, Task, TaskEvent } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

const POLL_INTERVAL_MS = 5000;
const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export function TaskProgressPanel({
  initialTask,
  initialEvents,
  initialSteps,
}: {
  initialTask: Task;
  initialEvents: TaskEvent[];
  initialSteps: AgentStep[];
}) {
  const [task, setTask] = useState(initialTask);
  const [events, setEvents] = useState(initialEvents);
  const [steps, setSteps] = useState(initialSteps);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);

  const shouldPoll = useMemo(() => !TERMINAL_STATUSES.has(task.status), [task.status]);
  const canRetryTask = task.status === "failed";
  const taskId = task.task_id;

  const refreshTaskProgress = useCallback(async () => {
    setRefreshing(true);
    setRefreshError(null);
    try {
      const [nextTask, nextEvents, nextSteps] = await Promise.all([
        getTask(taskId),
        getTaskEvents(taskId),
        getTaskSteps(taskId),
      ]);
      setTask(nextTask);
      setEvents(nextEvents);
      setSteps(nextSteps);
    } catch (exc) {
      if (exc instanceof ApiClientError) {
        setRefreshError(`${exc.code}: ${exc.message}`);
      } else {
        setRefreshError("任务进度刷新失败。");
      }
    } finally {
      setRefreshing(false);
    }
  }, [taskId]);

  const handleRetryTask = useCallback(async () => {
    if (!canRetryTask || retrying) {
      return;
    }
    setRetrying(true);
    setRetryMessage(null);
    setRetryError(null);
    try {
      await retryTask(taskId);
      setRetryMessage("重试任务已提交");
      await refreshTaskProgress();
    } catch (exc) {
      if (exc instanceof ApiClientError) {
        const traceText = exc.traceId ? `，trace id: ${exc.traceId}` : "";
        setRetryError(`重试失败：${exc.code}: ${exc.message}${traceText}`);
      } else {
        setRetryError("重试投递失败，请稍后再试。");
      }
    } finally {
      setRetrying(false);
    }
  }, [canRetryTask, refreshTaskProgress, retrying, taskId]);

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }
    const interval = window.setInterval(() => {
      void refreshTaskProgress();
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [refreshTaskProgress, shouldPoll]);

  return (
    <div className="space-y-6 p-6">
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-wide text-slate-500">
              {task.task_id} / {task.trace_id}
            </p>
            <p className="mt-2 text-sm text-slate-600">{task.target}</p>
            {task.error_code || task.error_message ? (
              <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {task.error_code ? `${task.error_code}: ` : ""}
                {task.error_message ?? "任务失败。"}
              </p>
            ) : null}
            {refreshError ? (
              <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
                {refreshError}
              </p>
            ) : null}
            {retryMessage ? (
              <p className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {retryMessage}
              </p>
            ) : null}
            {retryError ? (
              <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {retryError}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={task.status} />
            <span className="rounded border border-slate-200 px-2 py-1 font-mono text-[11px] uppercase text-slate-500">
              {formatDuration(task.duration_ms)}
            </span>
            <span className="rounded border border-slate-200 px-2 py-1 font-mono text-[11px] uppercase text-slate-500">
              {refreshing ? "刷新中" : shouldPoll ? "轮询中" : "已结束"}
            </span>
            <button
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
              type="button"
              onClick={() => void refreshTaskProgress()}
              disabled={refreshing}
            >
              刷新
            </button>
            {canRetryTask ? (
              <button
                className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-800 hover:bg-amber-100 disabled:cursor-not-allowed disabled:text-amber-400"
                type="button"
                onClick={() => void handleRetryTask()}
                disabled={retrying || refreshing}
              >
                {retrying ? "正在重新投递" : "重试任务"}
              </button>
            ) : null}
            {task.report_id ? (
              <Link
                href={`/reports/${task.report_id}`}
                className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-800"
              >
                打开报告
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      <TaskTimeline events={events} />
      <AgentStepsTable steps={steps} />
    </div>
  );
}
