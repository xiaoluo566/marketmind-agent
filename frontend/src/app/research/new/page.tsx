import { NewResearchForm } from "@/components/new-research-form";
import { PageHeader } from "@/components/page-header";

export default function NewResearchPage() {
  return (
    <>
      <PageHeader
        eyebrow="New Research"
        title="Create a competitor research task"
        description="Submit long-running research work to FastAPI and continue from the task timeline while Celery, crawler, RAG, and report stages run in the backend."
      />
      <div className="p-6">
        <NewResearchForm />
      </div>
    </>
  );
}
