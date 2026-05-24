import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { listReports } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

export default async function ReportsPage() {
  const reportItems = await listReports();

  return (
    <>
      <PageHeader
        eyebrow="Reports"
        title="Generated research reports"
        description="Browse structured competitor reports with risk scores, evidence counts, and source-linked conclusions."
      />
      <div className="grid gap-4 p-6 xl:grid-cols-2">
        {reportItems.map((report) => (
          <Link key={report.report_id} href={`/reports/${report.report_id}`} className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-200 hover:bg-blue-50/30">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-xs uppercase tracking-wide text-slate-500">
                  {report.report_id} / {report.task_id}
                </p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">{report.title}</h2>
              </div>
              <StatusBadge status={report.risk_level} />
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">{report.summary}</p>
            <div className="mt-4 flex flex-wrap gap-3 font-mono text-xs uppercase tracking-wide text-slate-500">
              <span>{report.evidence_count} evidence refs</span>
              <span>score {report.risk_score}</span>
              <span>{formatDateTime(report.created_at)}</span>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}

