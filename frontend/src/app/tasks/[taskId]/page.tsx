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
        eyebrow="Task detail"
        title={task.title}
        description="Review task state, trace ID, event timeline, Agent steps, and recovery actions."
      />
      <TaskProgressPanel initialTask={task} initialEvents={events} initialSteps={steps} />
    </>
  );
}
