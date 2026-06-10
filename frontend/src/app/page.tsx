import { Activity, Clock3, Database, ShieldCheck, TimerReset } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { getLLMOpsSummary, listReports, listServices, listTasks } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/utils";

export default async function DashboardPage() {
  const [taskItems, reportItems, serviceItems, llmopsSummary] = await Promise.all([
    listTasks(),
    listReports(),
    listServices(),
    getLLMOpsSummary(),
  ]);
  const completed = taskItems.filter((task) => task.status === "completed").length;
  const successRate = taskItems.length > 0 ? Math.round((completed / taskItems.length) * 100) : 0;
  const averageDuration = averageDurationMs(taskItems.map((task) => task.duration_ms));

  return (
    <>
      <PageHeader
        eyebrow="工作台"
        title="Agent 调研工作台"
        description="集中查看异步调研任务、采集状态、Agent 步骤、RAG 证据、LLMOps 指标和报告输出。"
      />
      <div className="space-y-6 p-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <StatCard label="今日任务" value={String(taskItems.length)} detail="演示数据集" icon={Activity} />
          <StatCard label="成功率" value={`${successRate}%`} detail="已完成任务" icon={ShieldCheck} />
          <StatCard label="平均耗时" value={formatDuration(averageDuration)} detail="端到端" icon={Clock3} />
          <StatCard label="排队中" value="2" detail="Worker 积压" icon={TimerReset} />
          <StatCard
            label="校验错误"
            value={String(llmopsSummary.guardrail_metrics.validation_error_count)}
            detail="结构化解析失败"
            icon={Database}
          />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-950">LLMOps 指标</h2>
              <p className="mt-1 text-xs text-slate-500">
                数据来源：任务 {sourceLabel(llmopsSummary.task_metrics.data_source)} / 模型{" "}
                {sourceLabel(llmopsSummary.model_usage.data_source)} / Provider{" "}
                {sourceLabel(llmopsSummary.provider_metrics.data_source)}
              </p>
            </div>
            <p className="text-xs text-slate-500">{formatDateTime(llmopsSummary.generated_at)}</p>
          </div>
          <div className="grid gap-4 p-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricBlock
              label="模型调用"
              value={String(llmopsSummary.model_usage.model_call_count)}
              detail={`Token 总量：${llmopsSummary.model_usage.total_tokens}`}
            />
            <MetricBlock
              label="结构化解析失败"
              value={String(llmopsSummary.guardrail_metrics.validation_error_count)}
              detail={`自愈次数：${llmopsSummary.guardrail_metrics.self_heal_count}`}
            />
            <MetricBlock
              label="自愈成功率"
              value={formatRate(llmopsSummary.guardrail_metrics.self_heal_success_rate)}
              detail="按校验失败次数计算"
            />
            <MetricBlock
              label="恢复成功率"
              value={formatRate(llmopsSummary.recovery_metrics.recovery_success_rate)}
              detail={`Retry：${llmopsSummary.recovery_metrics.retry_requested_count}`}
            />
          </div>
          <div className="border-t border-slate-100 px-4 py-3">
            <div className="flex flex-wrap gap-2 text-xs text-amber-700">
              {llmopsSummary.warnings.map((warning) => (
                <span key={warning} className="rounded-md bg-amber-50 px-2 py-1">
                  {warning}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-lg border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-950">最近任务</h2>
              <Link href="/tasks" className="text-sm font-medium text-blue-700 hover:text-blue-900">
                查看全部
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
              <h2 className="text-sm font-semibold text-slate-950">系统链路</h2>
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
            <h2 className="text-sm font-semibold text-slate-950">最近报告</h2>
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
                <p className="font-mono text-sm text-slate-700">{report.evidence_count} 条证据</p>
                <p className="text-sm text-slate-500">{formatDateTime(report.created_at)}</p>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

function MetricBlock({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function averageDurationMs(values: Array<number | undefined>) {
  const durations = values.filter((value): value is number => typeof value === "number" && value > 0);
  if (durations.length === 0) {
    return 0;
  }
  return Math.round(durations.reduce((total, item) => total + item, 0) / durations.length);
}

function formatRate(value: number) {
  return `${Math.round(value * 100)}%`;
}

function sourceLabel(source: string) {
  if (source.startsWith("database")) {
    return "数据库";
  }
  if (source.startsWith("mock")) {
    return "mock";
  }
  if (source.startsWith("not_persisted")) {
    return "未持久化";
  }
  return source;
}
