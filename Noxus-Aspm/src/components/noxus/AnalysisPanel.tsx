import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Play, RefreshCw, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  analysisRunsQuery,
  analysisStatusQuery,
  scansQuery,
  importFindings,
  startAnalysis,
} from "@/lib/noxus/api";

const statusLabels = {
  queued: "Na fila",
  running: "Executando",
  completed: "Concluída",
  failed: "Falhou",
  interrupted: "Interrompida",
};

export function AnalysisPanel({ allowImport = false }: { allowImport?: boolean }) {
  const client = useQueryClient();
  const status = useQuery(analysisStatusQuery);
  const runs = useQuery(analysisRunsQuery);
  const scans = useQuery({ ...scansQuery, enabled: allowImport });
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const refresh = () => client.invalidateQueries({ queryKey: ["noxus"] });
  const importer = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Escolha um arquivo JSON.");
      if (file.size > 10 * 1024 * 1024) throw new Error("O limite do arquivo é 10 MiB.");
      const value: unknown = JSON.parse(await file.text());
      if (
        typeof value !== "object" ||
        value === null ||
        !("findings" in value) ||
        !Array.isArray(value.findings) ||
        !("source" in value) ||
        !("asset" in value) ||
        !("scan" in value) ||
        !("developer" in value)
      ) {
        throw new Error(
          "Envie o envelope NOXUS 1.0 completo: source, developer, asset, scan e findings.",
        );
      }
      // Não extrair somente findings: o ativo, o produtor e a ferramenta pertencem ao envelope.
      return importFindings(value);
    },
    onSuccess: (result) => {
      setMessage(
        result.replayed
          ? `Varredura ${result.scan_id} já recebida. Reenvio idêntico, sem duplicação.`
          : `Varredura recebida: ${result.received} achados; ${result.created} novos, ${result.updated} atualizados e ${result.duplicates} repetidos.`,
      );
      void refresh();
    },
  });
  const runner = useMutation({
    mutationFn: () => startAnalysis(),
    onSuccess: () => {
      setMessage("Análise iniciada. O painel será atualizado automaticamente.");
      void refresh();
    },
  });
  const busy = runs.data?.some((run) => run.status === "running" || run.status === "queued");
  const error = importer.error || runner.error || runs.error || status.error || scans.error;

  return (
    <section className="panel mb-5 space-y-4 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Importação e triagem</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Importe um relatório e analise até 50 achados pendentes por execução.
            {status.data?.provider === "openrouter"
              ? " Ao analisar, o conteúdo do lote será enviado aos modelos da OpenRouter."
              : status.data?.provider === "ollama"
                ? " Modelo configurado via Ollama."
                : ""}
          </p>
          {status.data?.error && <p className="mt-2 text-xs text-medium">{status.data.error}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => void refresh()}>
            <RefreshCw /> Atualizar
          </Button>
          <Button
            size="sm"
            disabled={!status.data?.ready || busy || runner.isPending}
            onClick={() => runner.mutate()}
          >
            <Play /> {busy ? "Analisando…" : "Analisar pendentes"}
          </Button>
        </div>
      </div>
      {allowImport && (
        <div className="flex flex-wrap items-end gap-3 border-t border-border pt-4">
          <label className="flex min-w-56 flex-1 flex-col gap-2 text-xs">
            Relatório JSON
            <input
              type="file"
              accept=".json,application/json"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                importer.reset();
                setMessage("");
              }}
              className="rounded border border-border p-2"
            />
          </label>
          <Button
            variant="outline"
            disabled={!file || importer.isPending}
            onClick={() => importer.mutate()}
          >
            <Upload /> {importer.isPending ? "Importando…" : "Importar JSON"}
          </Button>
          <p className="w-full text-xs text-muted-foreground">
            Envelope NOXUS 1.0: source, developer, asset, scan e findings. O ativo vem de asset.id;
            a ferramenta, de scan.tool. Aceita varreduras sem achados e severidade null. Não envie
            relatórios brutos, código ou credenciais.
          </p>
        </div>
      )}
      {message && (
        <p role="status" className="text-xs text-success">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="text-xs text-critical">
          {error.message}
        </p>
      )}
      {allowImport && (
        <details className="rounded border border-border p-3 text-xs">
          <summary className="cursor-pointer">
            Varreduras recebidas ({scans.data?.length ?? 0})
          </summary>
          {!scans.data?.length && (
            <p className="mt-3 text-muted-foreground">Nenhuma varredura recebida.</p>
          )}
          {scans.data?.slice(0, 20).map((record) => (
            <div key={record.scan.id} className="mt-3 border-t border-border pt-3">
              <p>
                {record.asset.name} · {record.scan.tool} · {record.findings_count} achados
              </p>
              <p>
                {record.scan.status === "partial"
                  ? "Parcial"
                  : record.scan.status === "failed"
                    ? "Falhou"
                    : "Concluída"}{" "}
                · {record.source}
              </p>
              <code className="break-all">{record.scan.id}</code>
              <p>{new Date(record.scan.finished_at).toLocaleString("pt-BR")}</p>
              {record.scan.error && <p className="text-critical">{record.scan.error}</p>}
            </div>
          ))}
        </details>
      )}
      <div className="space-y-2">
        {!runs.data?.length && (
          <p className="text-xs text-muted-foreground">Nenhuma análise executada.</p>
        )}
        {runs.data?.slice(0, 8).map((run) => (
          <div key={run.id} className="rounded border border-border p-3 text-xs">
            <div className="flex flex-wrap justify-between gap-2">
              <span>
                {statusLabels[run.status]} · {run.findingIds.length} achados
              </span>
              <time>{new Date(run.createdAt).toLocaleString("pt-BR")}</time>
            </div>
            <code className="mt-1 block text-muted-foreground">{run.id}</code>
            {run.stage && <p className="mt-1">{run.stage}</p>}
            {run.error && <p className="mt-2 text-critical">{run.error}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
