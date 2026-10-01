import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/noxus/AppShell";
import { AssetRegistry } from "@/components/noxus/AssetRegistry";
import { DemoNotice } from "@/components/noxus/DemoNotice";
import { assetsQuery } from "@/lib/noxus/api";

export const Route = createFileRoute("/assets")({
  head: () => ({
    meta: [
      { title: "Aplicações e ativos — Noxus ASPM" },
      {
        name: "description",
        content: "Registro contextual de aplicações, ambientes e ativos monitorados pelo Noxus.",
      },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(assetsQuery),
  component: AssetsPage,
});

function AssetsPage() {
  const { data: assets } = useSuspenseQuery(assetsQuery);

  return (
    <AppShell
      title="Aplicações e ativos"
      subtitle="Inventário contextual para descoberta, revisão e priorização de riscos."
    >
      <DemoNotice />
      <AssetRegistry initialAssets={assets} />
    </AppShell>
  );
}
