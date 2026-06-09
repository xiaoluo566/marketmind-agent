import type { TaskStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  received: "border-slate-300 bg-slate-100 text-slate-700",
  queued: "border-slate-300 bg-slate-100 text-slate-700",
  running: "border-blue-200 bg-blue-50 text-blue-700",
  crawling: "border-blue-200 bg-blue-50 text-blue-700",
  reasoning: "border-blue-200 bg-blue-50 text-blue-700",
  retrieving: "border-teal-200 bg-teal-50 text-teal-700",
  reporting: "border-teal-200 bg-teal-50 text-teal-700",
  waiting_retry: "border-amber-200 bg-amber-50 text-amber-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  cancelled: "border-slate-300 bg-slate-100 text-slate-600",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending: "border-slate-300 bg-slate-100 text-slate-700",
  offline: "border-slate-300 bg-slate-100 text-slate-600",
  mock: "border-violet-200 bg-violet-50 text-violet-700",
  delayed: "border-amber-200 bg-amber-50 text-amber-700",
  healthy: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

const labels: Record<string, string> = {
  received: "已接收",
  queued: "排队中",
  running: "运行中",
  crawling: "采集中",
  reasoning: "推理中",
  retrieving: "检索中",
  reporting: "生成报告",
  waiting_retry: "等待重试",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  success: "成功",
  pending: "待处理",
  offline: "离线",
  mock: "模拟",
  delayed: "延迟",
  healthy: "健康",
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

export function StatusBadge({
  status,
  className,
}: {
  status: TaskStatus | string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-1 font-mono text-[11px] font-semibold uppercase tracking-wide",
        styles[status] ?? "border-slate-300 bg-slate-100 text-slate-700",
        className,
      )}
    >
      {labels[status] ?? status}
    </span>
  );
}
