import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { listTasks } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/utils";

export default async function TasksPage() {
  const taskItems = await listTasks();

  return (
    <>
      <PageHeader
        eyebrow="Tasks"
        title="Research task history"
        description="Track queued, running, failed, and completed research tasks with trace IDs and report links."
      />
      <div className="p-6">
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="bg-slate-50 text-left font-mono text-[11px] uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Task</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {taskItems.map((task) => (
                <tr key={task.task_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link href={`/tasks/${task.task_id}`} className="font-semibold text-slate-950 hover:text-blue-700">
                      {task.title}
                    </Link>
                    <p className="mt-1 font-mono text-xs text-slate-500">{task.task_id} / {task.trace_id}</p>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={task.status} /></td>
                  <td className="px-4 py-3 text-slate-600">{task.mode}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDuration(task.duration_ms)}</td>
                  <td className="px-4 py-3 text-slate-500">{formatDateTime(task.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

