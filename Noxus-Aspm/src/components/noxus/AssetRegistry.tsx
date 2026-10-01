import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  Boxes,
  CheckCircle2,
  ClipboardCheck,
  Globe2,
  MapPin,
  Plus,
  Settings2,
  ShieldQuestion,
} from "lucide-react";

import { AssetEditorSheet } from "@/components/noxus/AssetEditorSheet";
import { SeverityBadge } from "@/components/noxus/SeverityBadge";
import { StatCard } from "@/components/noxus/StatCard";
import { Button } from "@/components/ui/button";
import {
  assetAccessLabel,
  assetDataLabel,
  assetHostingLabel,
  assetSourceLabel,
  assetStatusLabel,
  assetTypeLabel,
  environmentLabel,
} from "@/lib/noxus/asset-labels";
import {
  assetsQuery,
  createAsset,
  dashboardQuery,
  toAssetUpdateRequest,
  toAssetWriteRequest,
  updateAsset,
} from "@/lib/noxus/api";
import type { Asset } from "@/lib/noxus/types";
import { relativeTime } from "@/lib/noxus/ui";
import { cn } from "@/lib/utils";

const statusClass: Record<Asset["registryStatus"], string> = {
  active: "border-success/30 bg-success/5 text-success",
  pending_review: "border-signal/30 bg-signal/5 text-signal",
  inactive: "border-border bg-muted text-muted-foreground",
};

const accessClass: Record<Asset["access"], string> = {
  unknown: "border-border bg-muted text-muted-foreground",
  public_internet: "border-critical/30 bg-critical/5 text-critical",
  restricted_internet: "border-medium/30 bg-medium/5 text-medium",
  private_network: "border-low/30 bg-low/5 text-low",
};

export function AssetRegistry({ initialAssets }: { initialAssets: Asset[] }) {
  const queryClient = useQueryClient();
  const assets = initialAssets;
  const [editorOpen, setEditorOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [feedback, setFeedback] = useState("");

  const manualAssets = assets.filter((asset) => asset.registrationSource === "manual").length;
  const automaticAssets = assets.length - manualAssets;
  const publiclyAccessibleAssets = assets.filter(
    (asset) => asset.access === "public_internet" && asset.registryStatus !== "inactive",
  ).length;
  const pendingReviewAssets = assets.filter(
    (asset) => asset.registryStatus === "pending_review",
  ).length;

  const openCreate = () => {
    setSelectedAsset(null);
    setEditorOpen(true);
  };

  const openEdit = (asset: Asset) => {
    setSelectedAsset(asset);
    setEditorOpen(true);
  };

  const saveAsset = async (asset: Asset) => {
    const alreadyExists = assets.some((current) => current.id === asset.id);
    const persistedAsset = alreadyExists
      ? await updateAsset(asset.id, toAssetUpdateRequest(asset))
      : await createAsset(toAssetWriteRequest(asset));
    setFeedback(`${persistedAsset.name} foi salvo.`);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: assetsQuery.queryKey }),
      queryClient.invalidateQueries({ queryKey: dashboardQuery.queryKey }),
    ]);
  };

  return (
    <>
      <section className="mb-5 flex flex-col gap-4 rounded-lg border border-border bg-card/70 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm font-medium">
            <ClipboardCheck className="size-4 text-primary" /> Gestão do inventário
          </p>
          <p className="mt-1 max-w-2xl text-xs text-muted-foreground">
            Os relatórios usam o ID estável de asset.id. Ativos novos entram para revisão do
            contexto de negócio, sem inferir dono, ambiente ou exposição.
          </p>
          {feedback ? (
            <p className="mt-2 flex items-center gap-1.5 text-xs text-success" aria-live="polite">
              <CheckCircle2 className="size-3.5" /> {feedback}
            </p>
          ) : null}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button onClick={openCreate}>
            <Plus /> Adicionar manualmente
          </Button>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label="Ativos cadastrados"
          value={String(manualAssets + automaticAssets)}
          icon={Boxes}
        />
        <StatCard
          label="Encontrados automaticamente"
          value={String(automaticAssets)}
          hint="inclui os pendentes e os já revisados"
          icon={Bot}
          tone="signal"
        />
        <StatCard
          label="Adicionados manualmente"
          value={String(manualAssets)}
          hint="cadastrados diretamente no inventário"
          icon={Plus}
        />
        <StatCard
          label="Acesso público"
          value={String(publiclyAccessibleAssets)}
          hint="sem exigir rede privada ou autenticação prévia"
          icon={Globe2}
          tone="critical"
        />
        <StatCard
          label="Revisão pendente"
          value={String(pendingReviewAssets)}
          hint="contexto do ativo ainda não confirmado"
          icon={ShieldQuestion}
          tone={pendingReviewAssets > 0 ? "signal" : "success"}
        />
      </div>

      <section className="panel mt-6 overflow-hidden">
        <div className="border-b border-border p-4">
          <h2 className="text-base font-semibold">Registro contextual</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Hospedagem, acesso e ambiente são dimensões independentes. Um repositório privado no
            GitHub, por exemplo, está em SaaS na internet, mas exige autenticação e pode atender
            vários ambientes.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1320px] text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                {[
                  "Aplicação / ativo",
                  "Recurso técnico",
                  "Responsabilidade",
                  "Localização e acesso",
                  "Dados e avaliação",
                  "",
                ].map((label) => (
                  <th key={label || "actions"} className="label-mono px-4 py-3 font-normal">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {assets.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-muted-foreground">
                    Nenhum ativo cadastrado. Use “Adicionar manualmente”.
                  </td>
                </tr>
              )}
              {assets.map((asset) => (
                <tr key={asset.id} className="border-b border-border/60 align-top last:border-0">
                  <td className="px-4 py-4">
                    <p className="font-medium">{asset.applicationName}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{asset.name}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 text-[10px]",
                          statusClass[asset.registryStatus],
                        )}
                      >
                        {assetStatusLabel[asset.registryStatus]}
                      </span>
                      <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
                        {assetSourceLabel[asset.registrationSource]}
                      </span>
                    </div>
                  </td>
                  <td className="max-w-[300px] px-4 py-4">
                    <p>{assetTypeLabel[asset.type]}</p>
                    <p className="mt-1 break-all font-mono text-xs text-muted-foreground">
                      {asset.identifier}
                    </p>
                    {asset.technologies.length > 0 ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {asset.technologies.map((technology) => (
                          <span
                            key={technology}
                            className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                          >
                            {technology}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-4">
                    <p>{asset.owner}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {environmentLabel[asset.environment]}
                    </p>
                    <div className="mt-2">
                      <SeverityBadge severity={asset.businessCriticality} />
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <p className="flex items-center gap-1.5">
                      <MapPin className="size-3.5 text-muted-foreground" />
                      {asset.location.provider}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {assetHostingLabel[asset.location.hosting]} · {asset.location.region}
                    </p>
                    <span
                      className={cn(
                        "mt-2 inline-flex rounded-full border px-2 py-0.5 text-[10px]",
                        accessClass[asset.access],
                      )}
                    >
                      {assetAccessLabel[asset.access]}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <p className="text-xs">
                      Dados {assetDataLabel[asset.dataClassification].toLowerCase()}
                      {asset.containsRealData === null
                        ? " · uso de dados reais não informado"
                        : asset.containsRealData
                          ? " · reais"
                          : " · sem dados reais"}
                    </p>
                    {asset.assessmentStatus === "assessed" ? (
                      <>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Risco ainda não calculado
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {asset.openFindings} achados · scan{" "}
                          {asset.lastScanAt ? relativeTime(asset.lastScanAt) : "não realizado"}
                        </p>
                      </>
                    ) : (
                      <p className="mt-2 flex items-center gap-1.5 text-xs text-signal">
                        <Bot className="size-3.5" /> Ainda não avaliado
                      </p>
                    )}
                    <p className="mt-1 text-[10px] text-muted-foreground">
                      visto {relativeTime(asset.lastSeenAt)}
                    </p>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openEdit(asset)}
                      aria-label={`Configurar ${asset.name}`}
                    >
                      <Settings2 /> Configurar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <AssetEditorSheet
        asset={selectedAsset}
        open={editorOpen}
        onOpenChange={setEditorOpen}
        onSave={saveAsset}
      />
    </>
  );
}
