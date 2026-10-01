import { cn } from "@/lib/utils";
import { severityClass, severityLabel, statusClass, statusLabel } from "@/lib/noxus/ui";
import type { FindingStatus, Severity } from "@/lib/noxus/types";

export function SeverityBadge({
  severity,
  className,
}: {
  severity: Severity | null;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 font-mono text-[11px] tracking-wide uppercase",
        severity ? severityClass[severity] : "border-border bg-muted text-muted-foreground",
        className,
      )}
    >
      {severity ? severityLabel[severity] : "Não informada"}
    </span>
  );
}

export function StatusBadge({ status }: { status: FindingStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs",
        statusClass[status],
      )}
    >
      {statusLabel[status]}
    </span>
  );
}
