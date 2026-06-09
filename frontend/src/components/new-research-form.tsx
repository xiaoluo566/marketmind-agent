"use client";

import { AlertCircle, CheckCircle2, Loader2, SendHorizontal } from "lucide-react";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiClientError, createTask, getApiBaseUrl, isRealApiEnabled } from "@/lib/api";
import type { TaskAccepted, TaskCreateInput } from "@/lib/types";

const sourceOptions: Array<{
  label: string;
  value: TaskCreateInput["source_type"];
}> = [
  { label: "演示数据集", value: "demo_dataset" },
  { label: "公开 URL 采集", value: "public_url" },
  { label: "CSV/JSON 上传", value: "manual_upload" },
];

const modeOptions = [
  { label: "竞品调研", value: "competitive_research" },
  { label: "完整报告", value: "complete_report" },
  { label: "差评分析", value: "review_risk_scan" },
  { label: "机会点扫描", value: "opportunity_analysis" },
  { label: "风险扫描", value: "risk_scan" },
];

export function NewResearchForm() {
  const router = useRouter();
  const [target, setTarget] = useState("demo://portable-espresso-maker-negative-reviews");
  const [sourceType, setSourceType] = useState<TaskCreateInput["source_type"]>("demo_dataset");
  const [mode, setMode] = useState("competitive_research");
  const [useRag, setUseRag] = useState(true);
  const [saveScreenshot, setSaveScreenshot] = useState(false);
  const [generateMarkdown, setGenerateMarkdown] = useState(true);
  const [autoRetry, setAutoRetry] = useState(false);
  const [acceptedTask, setAcceptedTask] = useState<TaskAccepted | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setAcceptedTask(null);
    setPending(true);
    try {
      const accepted = await createTask({
        target,
        mode,
        priority: "normal",
        source_type: sourceType,
        options: {
          use_rag: useRag,
          save_crawler_screenshot: saveScreenshot,
          export_format: generateMarkdown ? "markdown" : "json",
          auto_retry: autoRetry,
        },
      });
      setAcceptedTask(accepted);
      router.push(`/tasks/${accepted.task_id}`);
    } catch (exc) {
      if (exc instanceof ApiClientError) {
        setError(`${exc.code}: ${exc.message}`);
      } else {
        setError("任务提交失败，请检查 API 地址和后端状态。");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="grid gap-6 xl:grid-cols-[1fr_360px]" onSubmit={handleSubmit}>
      <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {isRealApiEnabled() ? "真实 API" : "模拟模式"}
          </p>
          <p className="mt-1 break-all text-sm text-slate-700">{getApiBaseUrl()}</p>
        </div>

        <label className="block">
          <span className="text-sm font-semibold text-slate-700">商品 URL 或数据集</span>
          <input
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="https://example.com/product/123 或 demo://reviews.csv"
            type="text"
            value={target}
            onChange={(event) => setTarget(event.target.value)}
            required
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">数据来源</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={sourceType}
              onChange={(event) =>
                setSourceType(event.target.value as TaskCreateInput["source_type"])
              }
            >
              {sourceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">分析模式</span>
            <select
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              {modeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <Toggle label="启用 RAG 检索" checked={useRag} onChange={setUseRag} />
          <Toggle
            label="保存采集截图"
            checked={saveScreenshot}
            onChange={setSaveScreenshot}
          />
          <Toggle
            label="生成 Markdown 报告"
            checked={generateMarkdown}
            onChange={setGenerateMarkdown}
          />
          <Toggle label="失败后自动重试" checked={autoRetry} onChange={setAutoRetry} />
        </div>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        ) : null}

        {acceptedTask ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="font-mono">{acceptedTask.task_id}</span>
          </div>
        ) : null}

        <button
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={pending}
        >
          {pending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <SendHorizontal className="h-4 w-4" aria-hidden="true" />
          )}
          创建任务
        </button>
      </section>

      <aside className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-950">请求载荷</h2>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-100">
{`POST /api/tasks
{
  "target": "${target || "..."}",
  "mode": "${mode}",
  "priority": "normal",
  "source_type": "${sourceType}",
  "options": {
    "use_rag": ${String(useRag)}
  }
}`}
        </pre>
      </aside>
    </form>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm text-slate-700">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 rounded border-slate-300 text-blue-600"
      />
      {label}
    </label>
  );
}
