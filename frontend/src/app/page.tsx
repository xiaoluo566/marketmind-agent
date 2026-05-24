import { Activity, Clock3, Database, ShieldCheck, TimerReset } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { listReports, listServices, listTasks } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/utils";

export default async function DashboardPage() {
  const [taskItems, reportItems, serviceItems] = await Promise.all([
    listTasks(),
    listReports(),
    listServices(),
  ]);
  const completed = taskItems.filter((task) => task.status === "completed").length;
  const successRate = Math.round((completed / taskItems.length) * 100);

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title="Agent research operations"
        description="Monitor async research jobs, crawler health, Agent state, RAG evidence, and report output from one control surface."
      />
      <div className="space-y-6 p-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <StatCard label="Tasks today" value={String(taskItems.length)} detail="mock dataset" icon={Activity} />
          <StatCard label="Success rate" value={`${successRate}%`} detail="completed tasks" icon={ShieldCheck} />
          <StatCard label="Avg duration" value="3m 22s" detail="end-to-end" icon={Clock3} />
          <StatCard label="Queued" value="2" detail="worker backlog" icon={TimerReset} />
          <StatCard label="Validation errors" value="3" detail="self-heal samples" icon={Database} />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-lg border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-950">Recent tasks</h2>
              <Link href="/tasks" className="text-sm font-medium text-blue-700 hover:text-blue-900">
                View all
              </Link>
            </div>
            <div className="divide-y divide-slate-100">
              {taskItems.slice(0, 5).map((task) => (
                <Link
                  key={task.task_id}
                  href={`/tasks/${task.task_id}`}
                  className="grid gap-3 px-4 py-3 hover:bg-slate-50 md:grid-cols-[1fr_120px_120px]"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{task.title}</p>
                    <p className="mt-1 font-mono text-xs text-slate-500">{task.task_id}</p>
                  </div>
                  <StatusBadge status={task.status} />
                  <p className="text-sm text-slate-600">{formatDuration(task.duration_ms)}</p>
                </Link>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-950">System chain</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {serviceItems.map((service) => (
                <div key={service.name} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-slate-950">{service.name}</p>
                    <p className="mt-1 text-xs text-slate-500">{service.detail}</p>
                  </div>
                  <StatusBadge status={service.status} />
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-4 py-3">
            <h2 className="text-sm font-semibold text-slate-950">Recent reports</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {reportItems.map((report) => (
              <Link
                key={report.report_id}
                href={`/reports/${report.report_id}`}
                className="grid gap-3 px-4 py-3 hover:bg-slate-50 md:grid-cols-[1fr_120px_120px_140px]"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-950">{report.title}</p>
                  <p className="mt-1 text-sm text-slate-600">{report.summary}</p>
                </div>
                <StatusBadge status={report.risk_level} />
                <p className="font-mono text-sm text-slate-700">{report.evidence_count} refs</p>
                <p className="text-sm text-slate-500">{formatDateTime(report.created_at)}</p>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

