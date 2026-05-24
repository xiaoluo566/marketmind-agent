import { PageHeader } from "@/components/page-header";

export default function NewResearchPage() {
  return (
    <>
      <PageHeader
        eyebrow="New Research"
        title="Create a competitor research task"
        description="This form is wired for the future FastAPI task endpoint. Today it uses mock mode while backend task creation is being built."
      />
      <div className="p-6">
        <form className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">Product URL or dataset</span>
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                placeholder="https://example.com/product/123 or demo://reviews.csv"
                type="text"
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">Data source</span>
                <select className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  <option>URL Crawl</option>
                  <option>CSV/JSON Upload</option>
                  <option>Demo Dataset</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">Analysis mode</span>
                <select className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  <option>Complete report</option>
                  <option>Poor review analysis</option>
                  <option>Opportunity scan</option>
                  <option>Risk scan</option>
                </select>
              </label>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {["Enable RAG retrieval", "Save crawler screenshot", "Generate Markdown report", "Auto retry on failure"].map(
                (label) => (
                  <label key={label} className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm text-slate-700">
                    <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-blue-600" />
                    {label}
                  </label>
                ),
              )}
            </div>

            <button className="inline-flex h-10 items-center justify-center rounded-lg bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800" type="button">
              Create task
            </button>
          </section>

          <aside className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-950">Submission contract</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The backend will persist the task, dispatch Celery work, and return a task_id
              immediately. Frontend should not run crawler or model logic.
            </p>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-100">
{`POST /api/tasks
{
  "target": "...",
  "mode": "complete_report",
  "priority": "normal",
  "options": {
    "use_rag": true
  }
}`}
            </pre>
          </aside>
        </form>
      </div>
    </>
  );
}

