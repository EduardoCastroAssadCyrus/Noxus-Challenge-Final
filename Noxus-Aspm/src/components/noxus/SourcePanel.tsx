import type { SourceBreakdown } from "@/lib/noxus/types";

const labels: Record<string, string> = {
  SAST: "Análise estática (SAST)",
  DAST: "Análise dinâmica (DAST)",
  SCA: "Dependências (SCA)",
  SECRET: "Segredos",
  EXTENSION: "Extensões VS Code",
  GUARDRAIL: "Guardrails",
};

export function SourcePanel({ sources }: { sources: SourceBreakdown[] }) {
  const max = Math.max(1, ...sources.map((s) => s.findings + s.reviewed));

  return (
    <div className="panel p-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <p className="label-mono">Origem dos achados</p>
        <p className="font-mono text-[11px] text-muted-foreground">
          <span className="text-signal">■</span> pendentes{" "}
          <span className="ml-2 opacity-60">■</span> analisados pela IA
        </p>
      </div>

      {sources.length === 0 && (
        <p className="mt-4 text-sm text-muted-foreground">Aguardando importação de relatórios.</p>
      )}
      <ul className="mt-4 flex flex-col gap-4">
        {sources.map((s) => {
          const total = s.findings + s.reviewed;
          return (
            <li key={s.source}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-sm">{labels[s.source] ?? s.source}</span>
                <span className="shrink-0 font-mono text-[11px]">
                  <span className="text-signal">{s.findings} pendentes</span>
                  <span className="mx-1.5 text-border">/</span>
                  <span className="text-muted-foreground">{s.reviewed} revisados</span>
                  <span className="ml-2 text-foreground/80">({total})</span>
                </span>
              </div>
              <div className="mt-1.5 flex h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-signal"
                  style={{ width: `${(s.findings / max) * 100}%` }}
                />
                <div
                  className="h-full bg-muted-foreground/30"
                  style={{ width: `${(s.reviewed / max) * 100}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
