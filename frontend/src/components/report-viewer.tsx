import Link from "next/link";

import type { Evidence, Report } from "@/lib/types";

import { EvidenceList } from "./evidence-list";
import { StatusBadge } from "./status-badge";

export function ReportViewer({ report, evidence }: { report: Report; evidence: Evidence[] }) {
  const linkedEvidence = evidence.filter((item) =>
    report.sections.some((section) => section.evidence_ids.includes(item.evidence_id)),
  );

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-500">
              {report.report_id} / {report.task_id}
            </p>
            <h2 className="mt-2 text-xl font-semibold text-slate-950">{report.title}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{report.summary}</p>
          </div>
          <div className="text-right">
            <StatusBadge status={report.risk_level} />
            <p className="mt-2 font-mono text-2xl font-semibold text-slate-950">
              {report.risk_score}
            </p>
            <p className="text-xs text-slate-500">风险评分</p>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        {report.sections.map((section) => (
          <article key={section.title} className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-slate-950">{section.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{section.body}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {section.evidence_ids.map((id) => (
                <Link
                  key={id}
                  href="/evidence"
                  className="rounded border border-slate-200 bg-slate-50 px-2 py-1 font-mono text-[11px] uppercase tracking-wide text-slate-600 hover:bg-slate-100"
                >
                  {id}
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section>
        <h3 className="mb-3 text-sm font-semibold text-slate-950">证据引用</h3>
        <EvidenceList items={linkedEvidence} />
      </section>
    </div>
  );
}
