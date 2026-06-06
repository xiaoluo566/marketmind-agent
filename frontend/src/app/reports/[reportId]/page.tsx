import { PageHeader } from "@/components/page-header";
import { ReportViewer } from "@/components/report-viewer";
import { getReport, getReportEvidence } from "@/lib/api";

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ reportId: string }>;
}) {
  const { reportId } = await params;
  const [report, evidence] = await Promise.all([getReport(reportId), getReportEvidence(reportId)]);

  return (
    <>
      <PageHeader
        eyebrow="Report detail"
        title={report.title}
        description="Structured report output with evidence references and risk reasoning."
      />
      <div className="p-6">
        <ReportViewer report={report} evidence={evidence} />
      </div>
    </>
  );
}
