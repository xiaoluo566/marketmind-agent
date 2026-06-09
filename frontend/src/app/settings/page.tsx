import { PageHeader } from "@/components/page-header";

const featureFlags = [
  { key: "enable_rag", label: "启用 RAG 检索" },
  { key: "enable_crawler_screenshot", label: "采集截图留存" },
  { key: "enable_agent_step_debug", label: "Agent 步骤调试" },
  { key: "enable_retry", label: "失败任务重试" },
];

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        eyebrow="设置"
        title="本地联调设置"
        description="配置前端使用的 API 地址、轮询间隔、运行环境和功能开关。"
      />
      <div className="p-6">
        <section className="max-w-3xl space-y-5 rounded-lg border border-slate-200 bg-white p-5">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">API 基础地址</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              defaultValue="http://localhost:8000"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">轮询间隔</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              defaultValue="3000"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            {featureFlags.map((flag) => (
              <label key={flag.key} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3 text-slate-700">
                <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-blue-600" />
                <span>
                  <span className="block text-sm font-semibold text-slate-800">{flag.label}</span>
                  <span className="mt-1 block font-mono text-[11px] text-slate-500">{flag.key}</span>
                </span>
              </label>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
