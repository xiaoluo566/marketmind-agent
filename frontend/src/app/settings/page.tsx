import { PageHeader } from "@/components/page-header";

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="Local integration settings"
        description="Frontend-facing settings for API base URL, polling interval, environment, and feature flags."
      />
      <div className="p-6">
        <section className="max-w-3xl space-y-5 rounded-lg border border-slate-200 bg-white p-5">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">API Base URL</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              defaultValue="http://localhost:8000"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Polling interval</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              defaultValue="3000"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            {["enable_rag", "enable_crawler_screenshot", "enable_agent_step_debug", "enable_retry"].map((flag) => (
              <label key={flag} className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 font-mono text-xs text-slate-700">
                <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-blue-600" />
                {flag}
              </label>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

