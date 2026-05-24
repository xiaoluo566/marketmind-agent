import Link from "next/link";

import { AgentStepsTable } from "@/components/agent-steps-table";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { TaskTimeline } from "@/components/task-timeline";
import { getTask, getTaskEvents, getTaskSteps } from "@/lib/api";
import { formatDuration } from "@/lib/utils";

export default async function TaskDetailPage({ params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const [task, events, steps] = await Promise.all([
    getTask(taskId),
    getTaskEvents(taskId),
    getTaskSteps(taskId),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Task detail"
        title={task.title}
        description="Review task state, trace ID, event timeline, Agent steps, and recovery actions."
      />
      <div className="space-y-6 p-6">
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-wide text-slate-500">
                {task.task_id} / {task.trace_id}
              </p>
              <p className="mt-2 text-sm text-slate-600">{task.target}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={task.status} />
              <span className="rounded border border-slate-200 px-2 py-1 font-mono text-[11px] uppercase text-slate-500">
                {formatDuration(task.duration_ms)}
              </span>
              {task.report_id ? (
                <Link href={`/reports/${task.report_id}`} className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-800">
                  Open report
                </Link>
              ) : null}
            </div>
          </div>
        </section>

        <TaskTimeline events={events} />
        <AgentStepsTable steps={steps} />
      </div>
    </>
  );
}

