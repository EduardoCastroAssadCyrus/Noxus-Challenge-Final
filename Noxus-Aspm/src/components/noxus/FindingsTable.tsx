import { GitMerge } from "lucide-react";
import { SeverityBadge, StatusBadge } from "./SeverityBadge";
import { relativeTime } from "@/lib/noxus/ui";
import type { Finding } from "@/lib/noxus/types";
import { analysisLabel } from "@/lib/noxus/ui";

export function FindingsTable({
  findings,
  onSelect,
}: {
  findings: Finding[];
  onSelect?: (finding: Finding) => void;
}) {
  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1120px] text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              {[
                "ID",
                "Vulnerabilidade",
                "Ativo",
                "Origem",
                "Severidade técnica",
                "Triagem por IA",
                "Status",
                "Recebido",
              ].map((h) => (
                <th key={h} className="label-mono px-4 py-3 font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {findings.length === 0 && (
              <tr>
                <td colSpan={8} className="p-8 text-center text-muted-foreground">
                  Nenhum achado disponível. Importe um relatório JSON ou ajuste os filtros.
                </td>
              </tr>
            )}
            {findings.map((f) => (
              <tr
                key={f.id}
                onClick={() => onSelect?.(f)}
                onKeyDown={(event) => {
                  if ((event.key === "Enter" || event.key === " ") && onSelect) {
                    event.preventDefault();
                    onSelect(f);
                  }
                }}
                tabIndex={onSelect ? 0 : undefined}
                aria-label={onSelect ? `Abrir detalhes de ${f.id}: ${f.title}` : undefined}
                className="cursor-pointer border-b border-border/60 transition-colors last:border-0 hover:bg-accent/50 focus-visible:bg-accent/50 focus-visible:outline-none"
              >
                <td title={f.id} className="px-4 py-3 font-mono text-xs text-muted-foreground">
                  {f.id.length > 20 ? `${f.id.slice(0, 15)}…` : f.id}
                </td>
                <td className="px-4 py-3">
                  <p className="font-medium">{f.title}</p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {f.cve ? <span className="font-mono text-high">{f.cve}</span> : null}
                    {f.file ? (
                      <span className="font-mono">
                        {f.file}
                        {f.line ? `:${f.line}` : ""}
                      </span>
                    ) : null}
                    {f.correlatedCount > 1 ? (
                      <span className="inline-flex items-center gap-1">
                        <GitMerge className="size-3" />
                        {f.correlatedCount} correlacionados
                      </span>
                    ) : null}
                  </p>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {f.assetName ?? "Não correlacionado"}
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs text-muted-foreground">
                    {f.source} · {f.tool}
                  </span>
                  {f.producer && <p className="mt-1 text-xs text-muted-foreground">{f.producer}</p>}
                </td>
                <td className="px-4 py-3">
                  <SeverityBadge severity={f.technicalSeverity} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs">
                      {f.analysis ? analysisLabel[f.analysis.classification] : "Pendente"}
                    </span>
                    {f.analysis && (
                      <span className="font-mono text-xs text-muted-foreground">
                        {Math.round(f.analysis.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={f.status} />
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {f.importedAt ? relativeTime(f.importedAt) : "Não informado"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
