import Link from "next/link";
import { Download, FileJson } from "lucide-react";

import { getReportEvidencePackageUrl, getReportMarkdownExportUrl } from "@/lib/api";
import type { Evidence, Report } from "@/lib/types";

import { EvidenceList } from "./evidence-list";
import { StatusBadge } from "./status-badge";

export function ReportViewer({ report, evidence }: { report: Report; evidence: Evidence[] }) {
  const linkedEvidence = evidence.filter((item) =>
    report.sections.some((section) => section.evidence_ids.includes(item.evidence_id)),
  );
  const markdownExportUrl = getReportMarkdownExportUrl(report, linkedEvidence);
  const evidencePackageUrl = getReportEvidencePackageUrl(report, linkedEvidence);

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
        <div className="mt-5 flex flex-wrap gap-3">
          <a
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 text-sm font-semibold text-blue-700 hover:bg-blue-100"
            href={markdownExportUrl}
            download={`marketmind-report-${report.report_id}.md`}
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            导出 Markdown
          </a>
          <a
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            href={evidencePackageUrl}
            download={`marketmind-evidence-${report.report_id}.json`}
          >
            <FileJson className="h-4 w-4" aria-hidden="true" />
            下载证据包
          </a>
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
