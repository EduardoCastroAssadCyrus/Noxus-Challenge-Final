import { Siren } from "lucide-react";
import { SeverityBadge } from "./SeverityBadge";
import { relativeTime } from "@/lib/noxus/ui";
import type { EmergencyAlert } from "@/lib/noxus/types";

export function AlertsFeed({ alerts }: { alerts: EmergencyAlert[] }) {
  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="flex items-center justify-between">
        <p className="label-mono flex items-center gap-2">
          <Siren className="size-3.5 text-critical" /> Alertas emergenciais
        </p>
        <span className="font-mono text-xs text-muted-foreground">
          {alerts.filter((a) => !a.acknowledged).length} pendentes
        </span>
      </div>

      <ul className="mt-4 flex flex-col gap-3">
        {alerts.map((a) => (
          <li
            key={a.id}
            className="rounded-md border border-border bg-surface-raised/60 p-3 transition-colors hover:border-signal/30"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium">{a.title}</p>
              <SeverityBadge severity={a.severity} />
            </div>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{a.detail}</p>
            <p className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{a.assetName}</span>
              <span>·</span>
              <span>{relativeTime(a.createdAt)}</span>
              {a.acknowledged ? (
                <span className="ml-auto text-success">reconhecido</span>
              ) : (
                <span className="ml-auto text-critical">ação necessária</span>
              )}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
