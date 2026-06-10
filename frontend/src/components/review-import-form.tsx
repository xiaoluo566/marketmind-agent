"use client";

import { AlertCircle, CheckCircle2, Loader2, Upload } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiClientError, importReviews } from "@/lib/api";
import type { ReviewImportInput, ReviewImportResult } from "@/lib/types";

const csvExample = [
  "review_id,product_title,rating,content,author,published_at,source_url",
  "rev-001,Desk Lamp,1,The hinge broke after two days,Alice,2026-05-01,https://example.test/rev-001",
  "rev-002,Desk Lamp,2,Shipping was slow and support ignored me,Bob,2026-05-02,https://example.test/rev-002",
].join("\n");

const jsonExample = JSON.stringify(
  {
    product_title: "Pet Fountain",
    source_url: "demo://pet-fountain/reviews.json",
    reviews: [
      {
        review_id: "rev-leak",
        rating: 1,
        content: "The pump leaks and the water smells bad.",
        author: "buyer-a",
      },
      {
        review_id: "rev-return",
        rating: 2,
        content: "Return process was slow and customer support never replied.",
        author: "buyer-b",
      },
    ],
  },
  null,
  2,
);

const formatOptions: Array<{ label: "CSV" | "JSON"; value: ReviewImportInput["format"] }> = [
  { label: "CSV", value: "csv" },
  { label: "JSON", value: "json" },
];

export function ReviewImportForm() {
  const [format, setFormat] = useState<ReviewImportInput["format"]>("csv");
  const [productTitle, setProductTitle] = useState("Desk Lamp");
  const [sourceUrl, setSourceUrl] = useState("demo://desk-lamp/reviews.csv");
  const [content, setContent] = useState(csvExample);
  const [result, setResult] = useState<ReviewImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function switchFormat(nextFormat: ReviewImportInput["format"]) {
    setFormat(nextFormat);
    if (nextFormat === "csv") {
      setProductTitle("Desk Lamp");
      setSourceUrl("demo://desk-lamp/reviews.csv");
      setContent(csvExample);
      return;
    }
    setProductTitle("Pet Fountain");
    setSourceUrl("demo://pet-fountain/reviews.json");
    setContent(jsonExample);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const imported = await importReviews({
        format,
        content,
        product_title: productTitle,
        source_url: sourceUrl || undefined,
      });
      setResult(imported);
    } catch (exc) {
      if (exc instanceof ApiClientError) {
        setError(`${exc.code}: ${exc.message}`);
      } else {
        setError("评论导入失败，请检查 API 地址、文件格式和后端状态。");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="grid gap-6 xl:grid-cols-[1fr_380px]" onSubmit={handleSubmit}>
      <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap gap-2">
          {formatOptions.map((option) => (
            <button
              key={option.value}
              className={
                format === option.value
                  ? "rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white"
                  : "rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              }
              type="button"
              onClick={() => switchFormat(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">商品名称</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              value={productTitle}
              onChange={(event) => setProductTitle(event.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">来源地址</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
            />
          </label>
        </div>

        <label className="block">
          <span className="text-sm font-semibold text-slate-700">原始评论内容</span>
          <textarea
            className="mt-2 min-h-[320px] w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs leading-5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            required
          />
        </label>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
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
            <Upload className="h-4 w-4" aria-hidden="true" />
          )}
          导入评论
        </button>
      </section>

      <aside className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
        <div>
          <h2 className="text-sm font-semibold text-slate-950">导入结果</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            导入成功后会生成 manual_upload 任务，并把评论写入 reviews，后续 RAG 和报告证据链可以继续使用同一个 task_id。
          </p>
        </div>

        {result ? (
          <div className="space-y-4">
            <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span className="font-mono">{result.task_id}</span>
            </div>
            <dl className="grid gap-3 text-sm">
              <ResultRow label="成功导入" value={String(result.imported_count)} />
              <ResultRow label="重复跳过" value={String(result.duplicate_count)} />
              <ResultRow label="错误行数" value={String(result.error_count)} />
              <ResultRow label="product_id" value={result.product_id} />
              <ResultRow label="review_external_ids" value={result.review_external_ids.join(", ")} />
              <ResultRow label="imported_count" value={String(result.imported_count)} />
              <ResultRow label="duplicate_count" value={String(result.duplicate_count)} />
              <ResultRow label="error_count" value={String(result.error_count)} />
            </dl>
            {result.errors.length > 0 ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs font-semibold text-amber-800">错误明细</p>
                <ul className="mt-2 space-y-1 text-xs text-amber-800">
                  {result.errors.map((item) => (
                    <li key={`${item.row_number}-${item.field}`}>
                      第 {item.row_number} 行 / {item.field}: {item.message}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            暂无导入结果。
          </div>
        )}
      </aside>
    </form>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 break-all font-mono text-sm text-slate-900">{value || "-"}</dd>
    </div>
  );
}
