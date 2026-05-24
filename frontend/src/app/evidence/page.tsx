import { EvidenceList } from "@/components/evidence-list";
import { PageHeader } from "@/components/page-header";
import { listEvidence } from "@/lib/api";

export default async function EvidencePage() {
  const evidenceItems = await listEvidence();

  return (
    <>
      <PageHeader
        eyebrow="Evidence"
        title="Semantic review retrieval"
        description="Inspect the review chunks, crawler artifacts, and Agent step evidence that will support reports."
      />
      <div className="grid gap-6 p-6 xl:grid-cols-[1fr_320px]">
        <section>
          <div className="mb-4 grid gap-3 md:grid-cols-[1fr_160px_160px]">
            <input
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="Search quality, shipping, returns, support..."
            />
            <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option>top_k: 8</option>
              <option>top_k: 16</option>
            </select>
            <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option>All ratings</option>
              <option>1-2 stars</option>
              <option>3 stars</option>
            </select>
          </div>
          <EvidenceList items={evidenceItems} />
        </section>
        <aside className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-950">Selected evidence</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Selection will be wired after the task and report APIs are implemented. The first
            backend contract will return evidence IDs and source URLs.
          </p>
        </aside>
      </div>
    </>
  );
}

