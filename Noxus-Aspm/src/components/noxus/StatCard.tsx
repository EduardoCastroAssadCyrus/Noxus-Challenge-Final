import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  icon: LucideIcon;
  tone?: "default" | "critical" | "success" | "signal";
}) {
  const toneClass = {
    default: "text-foreground",
    critical: "text-critical",
    success: "text-success",
    signal: "text-signal",
  }[tone];

  return (
    <div className="panel p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="label-mono">{label}</p>
        <Icon className={cn("size-4 opacity-70", toneClass)} />
      </div>
      <p className={cn("mt-3 font-mono text-3xl leading-none font-semibold", toneClass)}>{value}</p>
      {hint ? <p className="mt-2 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
