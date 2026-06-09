import { PageHeader } from "@/components/page-header";
import { TaskProgressPanel } from "@/components/task-progress-panel";
import { getTask, getTaskEvents, getTaskSteps } from "@/lib/api";

export default async function TaskDetailPage({ params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const [task, events, steps] = await Promise.all([
    getTask(taskId),
    getTaskEvents(taskId),
    getTaskSteps(taskId),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="任务详情"
        title={task.title}
        description="查看任务状态、Trace ID、事件时间线、Agent 步骤和恢复动作。"
      />
      <TaskProgressPanel initialTask={task} initialEvents={events} initialSteps={steps} />
    </>
  );
}
