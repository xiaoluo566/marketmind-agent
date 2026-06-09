import type { AgentStep } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

import { StatusBadge } from "./status-badge";

export function AgentStepsTable({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Agent 步骤</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-sm">
          <thead className="bg-slate-50 text-left font-mono text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">步骤</th>
              <th className="px-4 py-3">类型</th>
              <th className="px-4 py-3">工具</th>
              <th className="px-4 py-3">状态</th>
              <th className="px-4 py-3">耗时</th>
              <th className="px-4 py-3">观察结果</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {steps.length === 0 ? (
              <tr>
                <td className="px-4 py-5 text-sm text-slate-500" colSpan={6}>
                  暂无 Agent 步骤记录。
                </td>
              </tr>
            ) : null}
            {steps.map((step) => (
              <tr key={step.step_id}>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">#{step.step_index}</td>
                <td className="px-4 py-3 text-slate-700">{step.step_type}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-600">
                  {step.tool_name ?? "-"}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={step.status} />
                </td>
                <td className="px-4 py-3 text-slate-600">{formatDuration(step.duration_ms)}</td>
                <td className="max-w-md px-4 py-3 text-slate-700">
                  {step.observation_summary ?? step.input_summary ?? step.error_code ?? "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
