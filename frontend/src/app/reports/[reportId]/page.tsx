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
        eyebrow="报告详情"
        title={report.title}
        description="查看结构化报告、证据引用和风险推理链路。"
      />
      <div className="p-6">
        <ReportViewer report={report} evidence={evidence} />
      </div>
    </>
  );
}
