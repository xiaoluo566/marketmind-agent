import type { AgentStep } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

import { StatusBadge } from "./status-badge";

export function AgentStepsTable({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Agent steps</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-sm">
          <thead className="bg-slate-50 text-left font-mono text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Step</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Tool</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Observation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {steps.map((step) => (
              <tr key={`${step.agent_run_id}-${step.step_index}`}>
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

