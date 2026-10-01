import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { SeverityBadge, StatusBadge } from "./SeverityBadge";
import { analysisLabel, relativeTime } from "@/lib/noxus/ui";
import type { Finding } from "@/lib/noxus/types";

export function FindingDrawer({
  finding,
  onOpenChange,
}: {
  finding: Finding | null;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={Boolean(finding)} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto border-border bg-surface sm:max-w-xl">
        {finding && (
          <>
            <SheetHeader>
              <SheetTitle>{finding.title}</SheetTitle>
              <SheetDescription>
                {finding.id} · {finding.tool} · {finding.assetName ?? "Sem ativo associado"}
              </SheetDescription>
            </SheetHeader>
            <div className="space-y-6 p-4 text-sm">
              <div className="flex gap-3">
                <SeverityBadge severity={finding.technicalSeverity} />
                <StatusBadge status={finding.status} />
              </div>
              {finding.scanId && (
                <section className="space-y-2 break-all rounded border border-border p-3 text-xs">
                  <p>
                    Produtor: {finding.producer} · Categoria: {finding.source}
                  </p>
                  <p>Varredura: {finding.scanId}</p>
                  <p>Ocorrências em varreduras: {finding.occurrences}</p>
                  <p className="text-muted-foreground">
                    O campo developer identifica quem executou a análise, não quem introduziu a
                    falha. Contexto, CWE/CVE, localização e dependência estão no JSON abaixo.
                  </p>
                </section>
              )}
              {finding.source === "SECRET" && (
                <p className="text-medium">
                  Textos livres de credenciais foram removidos antes do armazenamento e da análise
                  por IA.
                </p>
              )}
              <section>
                <p className="label-mono">Descrição original</p>
                <p className="mt-2 whitespace-pre-wrap">
                  {finding.description || "Não informada."}
                </p>
              </section>
              <section className="rounded border border-signal/30 p-4">
                <p className="label-mono">Triagem por IA</p>
                {finding.analysis ? (
                  <div className="mt-3 space-y-3">
                    <p className="font-semibold text-signal">
                      {analysisLabel[finding.analysis.classification]}
                    </p>
                    <p>
                      Confiança estimada pelo modelo:{" "}
                      {Math.round(finding.analysis.confidence * 100)}%
                    </p>
                    <p className="whitespace-pre-wrap">{finding.analysis.reason}</p>
                    <ul className="list-disc space-y-1 pl-4">
                      {finding.analysis.evidence.map((e, index) => (
                        <li key={index}>{e}</li>
                      ))}
                    </ul>
                    <p className="text-xs text-muted-foreground">
                      Sugestão para revisão humana. O achado original não foi excluído nem
                      resolvido.
                    </p>
                    <p className="break-all font-mono text-xs">
                      Execução: {finding.analysis.runId}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {relativeTime(finding.analysis.analyzedAt)}
                    </p>
                  </div>
                ) : (
                  <p className="mt-2 text-muted-foreground">Ainda não analisado.</p>
                )}
              </section>
              <section>
                <p className="label-mono">Correção informada na origem</p>
                <p className="mt-2">{finding.remediation || "Não informada."}</p>
              </section>
              <section>
                <p className="label-mono">Prioridade operacional</p>
                <p className="mt-2">{finding.priorityExplanation}</p>
              </section>
              {finding.file && (
                <p className="break-all font-mono">
                  {finding.file}
                  {finding.line ? `:${finding.line}` : ""}
                </p>
              )}
              <details className="rounded border border-border p-3">
                <summary className="cursor-pointer">
                  {finding.source === "SECRET"
                    ? "JSON sanitizado e contexto da varredura"
                    : "JSON original preservado e contexto da varredura"}
                </summary>
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-all text-xs">
                  {JSON.stringify(finding.original, null, 2)}
                </pre>
              </details>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
