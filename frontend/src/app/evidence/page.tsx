import { EvidenceList } from "@/components/evidence-list";
import { PageHeader } from "@/components/page-header";
import { listEvidence } from "@/lib/api";

export default async function EvidencePage() {
  const evidenceItems = await listEvidence();

  return (
    <>
      <PageHeader
        eyebrow="证据链"
        title="评论语义检索"
        description="查看支撑报告的评论切片、采集 artifact 和 Agent 步骤证据。"
      />
      <div className="grid gap-6 p-6 xl:grid-cols-[1fr_320px]">
        <section>
          <div className="mb-4 grid gap-3 md:grid-cols-[1fr_160px_160px]">
            <input
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="搜索质量差、物流慢、退货、售后等问题..."
            />
            <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option>top_k: 8</option>
              <option>top_k: 16</option>
            </select>
            <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option>全部评分</option>
              <option>1-2 星</option>
              <option>3 星</option>
            </select>
          </div>
          <EvidenceList items={evidenceItems} />
        </section>
        <aside className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-950">已选证据</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            证据选择会在任务和报告 API 完整接入后继续完善。当前后端契约已经返回证据 ID 和来源 URL。
          </p>
        </aside>
      </div>
    </>
  );
}
