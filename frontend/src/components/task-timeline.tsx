import type { TaskEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

import { StatusBadge } from "./status-badge";

export function TaskTimeline({ events }: { events: TaskEvent[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Event timeline</h2>
      </div>
      <div className="divide-y divide-slate-100">
        {events.map((event) => (
          <div key={event.event_id} className="grid gap-3 px-4 py-3 md:grid-cols-[140px_120px_1fr]">
            <span className="font-mono text-xs text-slate-500">{formatDateTime(event.created_at)}</span>
            <StatusBadge status={event.status} />
            <div>
              <p className="font-mono text-xs uppercase tracking-wide text-slate-500">
                {event.module} / {event.event_type}
              </p>
              <p className="mt-1 text-sm text-slate-700">{event.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

