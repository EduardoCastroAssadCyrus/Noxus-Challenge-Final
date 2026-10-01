import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/noxus/AppShell";
import { AnalysisPanel } from "@/components/noxus/AnalysisPanel";

export const Route = createFileRoute("/integrations")({
  head: () => ({ meta: [{ title: "Integrações — Noxus ASPM" }] }),
  component: IntegrationsPage,
});

function IntegrationsPage() {
  return (
    <AppShell
      title="Integrações"
      subtitle="NoxusAgent, API local em JSON e análise pelo Challenge3."
    >
      <AnalysisPanel />
      <section className="panel mb-4 p-4">
        <h2 className="font-semibold">Noxus Extension for IDE</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Base Sonar incorporada ao projeto. Os alertas da IDE aguardam 10 segundos sem edição. O
          envio automático de relatórios ao dashboard ainda não está habilitado.
        </p>
      </section>
      <section className="panel p-4">
        <h2 className="font-semibold">Entrada de dados</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Envie seus relatórios normalizados pela página de
          <Link to="/findings" className="mx-1 text-signal underline">
            Vulnerabilidades
          </Link>
          ou execute o NoxusAgent pelo terminal. Ele envia os envelopes para POST /api/findings
          neste mesmo backend, com autenticação local. Não inicie a API separada do Agent.
        </p>
        <div className="mt-4 space-y-2 rounded border border-border p-3 text-sm">
          <p>Na raiz do Noxus, com o backend aberto:</p>
          <p>
            <code>bun run agent:init</code> — cadastro inicial do projeto e executor.
          </p>
          <p>
            <code>bun run agent:scan --tools semgrep gitleaks</code> — varredura manual.
          </p>
          <p>
            <code>bun run agent:watch</code> — monitoramento contínuo; Ctrl+C encerra.
          </p>
          <p>
            <code>bun run agent:flush</code> — reenvio dos relatórios pendentes.
          </p>
          <p className="text-xs text-muted-foreground">
            Os scanners precisam estar instalados. A página não inicia processos. A triagem por IA
            continua sendo solicitada em “Analisar pendentes”.
          </p>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Chatbot e descoberta automática de ativos ainda não estão conectados.
        </p>
      </section>
    </AppShell>
  );
}
