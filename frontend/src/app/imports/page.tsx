import { PageHeader } from "@/components/page-header";
import { ReviewImportForm } from "@/components/review-import-form";

export default function ReviewImportsPage() {
  return (
    <>
      <PageHeader
        eyebrow="评论导入"
        title="CSV/JSON 评论导入"
        description="把店铺后台、第三方工具或人工整理的评论文件导入系统，形成可追踪的 manual_upload 任务，为 RAG 检索和证据链报告提供真实输入。"
      />
      <div className="p-6">
        <ReviewImportForm />
      </div>
    </>
  );
}
