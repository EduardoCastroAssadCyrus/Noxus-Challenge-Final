import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/noxus/AppShell";
import { FindingsTable } from "@/components/noxus/FindingsTable";
import { FindingDrawer } from "@/components/noxus/FindingDrawer";
import { AnalysisPanel } from "@/components/noxus/AnalysisPanel";
import { findingsQuery } from "@/lib/noxus/api";
import { analysisLabel, severityLabel } from "@/lib/noxus/ui";
import type { FindingAnalysis, Severity } from "@/lib/noxus/types";

export const Route = createFileRoute("/findings")({
  head: () => ({ meta: [{ title: "Vulnerabilidades — Noxus ASPM" }] }),
  loader: ({ context }) => context.queryClient.ensureQueryData(findingsQuery),
  component: FindingsPage,
});

function FindingsPage() {
  const { data: findings } = useSuspenseQuery(findingsQuery);
  const [classification, setClassification] = useState("all");
  const [source, setSource] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = findings.find((finding) => finding.id === selectedId) ?? null;
  const filtered = findings.filter(
    (f) =>
      (classification === "all" ||
        (classification === "pending"
          ? !f.analysis
          : f.analysis?.classification === classification)) &&
      (source === "all" || f.source === source) &&
      (severity === "all" || (f.technicalSeverity ?? "unknown") === severity) &&
      [f.id, f.title, f.tool, f.file, f.assetName]
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase()),
  );

  return (
    <AppShell
      title="Vulnerabilidades"
      subtitle="Dados originais e classificações da IA, com evidências preservadas."
    >
      <AnalysisPanel allowImport />
      <div className="mb-4 flex flex-wrap items-end gap-3 text-xs">
        <label className="flex flex-col gap-2">
          Triagem por IA
          <select
            className="rounded border border-border bg-background p-2"
            value={classification}
            onChange={(e) => setClassification(e.target.value)}
          >
            <option value="all">Todos os originais ({findings.length})</option>
            <option value="pending">Pendentes</option>
            {(Object.keys(analysisLabel) as FindingAnalysis["classification"][]).map((key) => (
              <option key={key} value={key}>
                {analysisLabel[key]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-2">
          Origem
          <select
            className="rounded border border-border bg-background p-2"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="all">Todas</option>
            {[...new Set(findings.map((f) => f.source))].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-2">
          Severidade técnica
          <select
            className="rounded border border-border bg-background p-2"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="all">Todas</option>
            {(Object.keys(severityLabel) as Severity[]).map((s) => (
              <option key={s} value={s}>
                {severityLabel[s]}
              </option>
            ))}
            <option value="unknown">Não informada</option>
          </select>
        </label>
        <label className="flex flex-1 flex-col gap-2">
          Buscar
          <input
            className="rounded border border-border bg-background p-2"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Título, arquivo, ID ou ferramenta"
          />
        </label>
        <span className="p-2 text-muted-foreground">{filtered.length} encontrados</span>
      </div>
      <FindingsTable findings={filtered} onSelect={(finding) => setSelectedId(finding.id)} />
      <FindingDrawer finding={selected} onOpenChange={(open) => !open && setSelectedId(null)} />
    </AppShell>
  );
}
