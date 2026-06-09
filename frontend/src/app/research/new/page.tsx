import { NewResearchForm } from "@/components/new-research-form";
import { PageHeader } from "@/components/page-header";

export default function NewResearchPage() {
  return (
    <>
      <PageHeader
        eyebrow="新建调研"
        title="创建竞品调研任务"
        description="提交长任务到 FastAPI，拿到 task_id 后通过任务时间线持续查看 Celery、采集、RAG 和报告阶段。"
      />
      <div className="p-6">
        <NewResearchForm />
      </div>
    </>
  );
}
