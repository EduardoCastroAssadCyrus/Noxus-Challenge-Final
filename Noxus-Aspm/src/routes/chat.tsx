import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/noxus/AppShell";

export const Route = createFileRoute("/chat")({
  head: () => ({ meta: [{ title: "Chatbot — Noxus ASPM" }] }),
  component: ChatPage,
});
function ChatPage() {
  return (
    <AppShell title="Chatbot de Risco" subtitle="Integração de conversa ainda não configurada.">
      <section className="panel p-6 text-sm text-muted-foreground">
        A triagem dos achados está disponível em Vulnerabilidades e Equipe Agêntica. O chatbot será
        conectado separadamente; não há respostas simuladas.
      </section>
    </AppShell>
  );
}
