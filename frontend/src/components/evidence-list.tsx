import type { Evidence } from "@/lib/types";
import { percent } from "@/lib/utils";

export function EvidenceList({ items }: { items: Evidence[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <article key={item.evidence_id} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-500">
                {item.evidence_id} / {item.source_type}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-700">{item.content}</p>
            </div>
            <span className="rounded border border-teal-200 bg-teal-50 px-2 py-1 font-mono text-[11px] font-semibold uppercase text-teal-700">
              {percent(item.similarity)}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 font-mono text-[11px] uppercase tracking-wide text-slate-500">
            <span>{item.source_url}</span>
            {item.rating ? <span>rating {item.rating}/5</span> : null}
            <span>{item.task_id}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

