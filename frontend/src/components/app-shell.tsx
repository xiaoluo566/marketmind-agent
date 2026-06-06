"use client";

import {
  Activity,
  FileText,
  LayoutDashboard,
  ListChecks,
  PlusCircle,
  RefreshCw,
  Search,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { getApiBaseUrl, getApiModeLabel, isRealApiEnabled } from "@/lib/api";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/research/new", label: "New Research", icon: PlusCircle },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/evidence", label: "Evidence", icon: Search },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const realApiEnabled = isRealApiEnabled();
  const apiModeLabel = getApiModeLabel();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[240px_1fr]">
        <aside className="border-r border-slate-200 bg-white">
          <div className="flex h-16 items-center border-b border-slate-200 px-5">
            <div>
              <p className="text-sm font-semibold text-slate-950">MarketMind Agent</p>
              <p className="font-mono text-[11px] uppercase tracking-wide text-slate-500">
                Evidence cockpit
              </p>
            </div>
          </div>
          <nav className="space-y-1 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                    active
                      ? "bg-blue-50 text-blue-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
            <div className="flex items-center gap-3">
              <Activity className="h-4 w-4 text-blue-700" aria-hidden="true" />
              <div>
                <p className="text-sm font-semibold text-slate-950">Local Dev</p>
                <p className="font-mono text-[11px] uppercase tracking-wide text-slate-500">
                  {realApiEnabled ? getApiBaseUrl() : "API mock client active"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "hidden rounded border px-2 py-1 font-mono text-[11px] font-semibold uppercase sm:inline-flex",
                  realApiEnabled
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-violet-200 bg-violet-50 text-violet-700",
                )}
              >
                {apiModeLabel}
              </span>
              <span className="hidden rounded border border-slate-200 bg-slate-50 px-2 py-1 font-mono text-[11px] font-semibold uppercase text-slate-600 sm:inline-flex">
                OpenAI-compatible
              </span>
              <button
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                type="button"
                aria-label="Refresh"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </header>
          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
}
