import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Bug, ShieldAlert, Sparkles, Boxes } from "lucide-react";
import { AppShell } from "@/components/noxus/AppShell";
import { ClearReportsButton } from "@/components/noxus/ClearReportsButton";
import { StatCard } from "@/components/noxus/StatCard";
import { TrendChart } from "@/components/noxus/TrendChart";
import { FindingsTable } from "@/components/noxus/FindingsTable";
import { AssetRiskList } from "@/components/noxus/AssetRiskList";
import { SourcePanel } from "@/components/noxus/SourcePanel";
import { FindingDrawer } from "@/components/noxus/FindingDrawer";
import { DemoNotice } from "@/components/noxus/DemoNotice";
import { Button } from "@/components/ui/button";
import { dashboardQuery } from "@/lib/noxus/api";
import type { Finding } from "@/lib/noxus/types";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Cérebro Central — Noxus ASPM" }] }),
  loader: ({ context }) => context.queryClient.ensureQueryData(dashboardQuery),
  component: Dashboard,
});

function Dashboard() {
  const { data } = useSuspenseQuery(dashboardQuery);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { metrics } = data;
  const selected = data.findings.find((f) => f.id === selectedId) ?? null;
  const order = { critical: 5, high: 4, medium: 3, low: 2, info: 1, unknown: 0 };
  const findings = [...data.findings]
    .sort(
      (a, b) => order[b.technicalSeverity ?? "unknown"] - order[a.technicalSeverity ?? "unknown"],
    )
    .slice(0, 8);
  const select = (finding: Finding) => setSelectedId(finding.id);

  return (
    <AppShell
      title="Cérebro Central"
      subtitle="Achados recebidos, ativos cadastrados e resultados de triagem por IA."
      actions={
        <div className="flex flex-wrap gap-2">
          <ClearReportsButton />
          <Button asChild size="sm">
            <Link to="/findings">Importar e analisar</Link>
          </Button>
        </div>
      }
    >
      <DemoNotice />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Achados recebidos"
          value={String(data.findings.length)}
          hint={`${metrics.pendingAnalysis} aguardando IA`}
          icon={Bug}
        />
        <StatCard
          label="Críticos abertos"
          value={String(metrics.criticalFindings)}
          hint="severidade técnica informada na origem"
          icon={ShieldAlert}
          tone="critical"
        />
        <StatCard
          label="Analisados pela IA"
          value={String(metrics.alertsReviewed)}
          hint={`${metrics.inconclusive} inconclusivos`}
          icon={Sparkles}
          tone="signal"
        />
        <StatCard
          label="Ativos ativos"
          value={String(metrics.monitoredAssets)}
          hint="cadastrados no inventário"
          icon={Boxes}
        />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Prováveis verdadeiros positivos"
          value={String(metrics.truePositives)}
          hint="sugestão da IA; evidências preservadas"
          icon={ShieldAlert}
        />
        <StatCard
          label="Possíveis falsos positivos"
          value={String(metrics.falsePositives)}
          hint="continuam disponíveis para revisão"
          icon={Sparkles}
          tone="signal"
        />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <section className="panel min-w-0 p-4 lg:col-span-2">
          <p className="label-mono">Achados recebidos por dia · severidade técnica</p>
          <TrendChart data={data.trend} />
        </section>
        <AssetRiskList assets={data.assets} />
      </div>
      <div className="mt-4">
        <SourcePanel sources={data.sources} />
      </div>
      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Achados por severidade técnica</h2>
        <FindingsTable findings={findings} onSelect={select} />
      </section>
      <FindingDrawer finding={selected} onOpenChange={(open) => !open && setSelectedId(null)} />
    </AppShell>
  );
}
