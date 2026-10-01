import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/noxus/AppShell";
import { AnalysisPanel } from "@/components/noxus/AnalysisPanel";

export const Route = createFileRoute("/agents")({
  head: () => ({ meta: [{ title: "Equipe agêntica — Noxus ASPM" }] }),
  component: AgentsPage,
});

function AgentsPage() {
  return (
    <AppShell
      title="Equipe Agêntica"
      subtitle="Execuções do Challenge3 e resultados registrados no seu computador."
    >
      <AnalysisPanel />
      <p className="text-sm text-muted-foreground">
        Cada execução percorre análise de vulnerabilidades, revisão, classificação e validação
        final. As sugestões podem ser verdadeiro positivo, falso positivo ou inconclusivo. Os
        achados originais permanecem disponíveis em Vulnerabilidades.
      </p>
    </AppShell>
  );
}
