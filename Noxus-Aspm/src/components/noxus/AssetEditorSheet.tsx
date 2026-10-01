import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  assetAccessLabel,
  assetDataLabel,
  assetHostingLabel,
  assetStatusLabel,
  assetTypeLabel,
  environmentLabel,
  severityLabel,
} from "@/lib/noxus/asset-labels";
import type {
  Asset,
  AssetAccess,
  AssetDataClassification,
  AssetHosting,
  AssetRegistryStatus,
  AssetType,
  EnvironmentType,
  Severity,
} from "@/lib/noxus/types";

interface AssetEditorSheetProps {
  asset: Asset | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (asset: Asset) => Promise<void> | void;
}

const selectClassName =
  "flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring";

function createEmptyAsset(): Asset {
  const now = new Date().toISOString();

  return {
    id: "",
    name: "",
    applicationName: "",
    type: "service",
    identifier: "",
    repo: "",
    environment: "development",
    owner: "",
    businessCriticality: "medium",
    access: "private_network",
    location: { hosting: "public_cloud", provider: "", region: "" },
    dataClassification: "internal",
    containsRealData: false,
    technologies: [],
    registrationSource: "manual",
    registryStatus: "active",
    discoveryConfidence: null,
    assessmentStatus: "not_assessed",
    riskScore: null,
    openFindings: 0,
    lastScanAt: null,
    lastSeenAt: now,
    compliance: null,
  };
}

export function AssetEditorSheet({ asset, open, onOpenChange, onSave }: AssetEditorSheetProps) {
  const [draft, setDraft] = useState<Asset>(() => asset ?? createEmptyAsset());
  const [technologyInput, setTechnologyInput] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;

    const nextDraft = asset ? structuredClone(asset) : createEmptyAsset();
    setDraft(nextDraft);
    setTechnologyInput(nextDraft.technologies.join(", "));
    setSaveError("");
  }, [asset, open]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setSaveError("");

    try {
      // Enviamos somente os campos editáveis; a API define ID, datas e avaliação.
      await onSave({
        ...draft,
        // Salvar a revisão confirma o contexto; a origem permanece a mesma.
        registryStatus:
          asset?.registryStatus === "pending_review" && draft.registryStatus === "pending_review"
            ? "active"
            : draft.registryStatus,
        technologies: technologyInput
          .split(",")
          .map((technology) => technology.trim())
          .filter(Boolean),
      });
      onOpenChange(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Não foi possível salvar o ativo.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle>{asset ? "Configurar ativo" : "Adicionar ativo manualmente"}</SheetTitle>
          <SheetDescription>
            Preencha o contexto conhecido. Campos técnicos poderão ser confirmados por integrações
            no futuro.
          </SheetDescription>
        </SheetHeader>

        <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
          <fieldset className="grid gap-4 sm:grid-cols-2">
            <legend className="label-mono col-span-full mb-1">IDENTIFICAÇÃO</legend>
            <Field label="Nome do ativo" htmlFor="asset-name">
              <Input
                id="asset-name"
                required
                value={draft.name}
                onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                placeholder="Ex.: API de Clientes"
              />
            </Field>
            <Field label="Aplicação ou produto" htmlFor="asset-application">
              <Input
                id="asset-application"
                required
                value={draft.applicationName}
                onChange={(event) => setDraft({ ...draft, applicationName: event.target.value })}
                placeholder="Ex.: Customer 360"
              />
            </Field>
            <Field label="Tipo" htmlFor="asset-type">
              <select
                id="asset-type"
                className={selectClassName}
                value={draft.type}
                onChange={(event) => setDraft({ ...draft, type: event.target.value as AssetType })}
              >
                {Object.entries(assetTypeLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Identificador verificável" htmlFor="asset-identifier">
              <Input
                id="asset-identifier"
                required
                value={draft.identifier}
                onChange={(event) => setDraft({ ...draft, identifier: event.target.value })}
                placeholder="URL, ARN, hostname ou URN"
              />
            </Field>
            <Field label="Repositório relacionado" htmlFor="asset-repo">
              <Input
                id="asset-repo"
                value={draft.repo}
                onChange={(event) => setDraft({ ...draft, repo: event.target.value })}
                placeholder="organização/repositório (opcional)"
              />
            </Field>
            <Field label="Responsável" htmlFor="asset-owner">
              <Input
                id="asset-owner"
                required
                value={draft.owner}
                onChange={(event) => setDraft({ ...draft, owner: event.target.value })}
                placeholder="Squad ou time proprietário"
              />
            </Field>
          </fieldset>

          <fieldset className="grid gap-4 sm:grid-cols-2">
            <legend className="label-mono col-span-full mb-1">LOCALIZAÇÃO E ACESSO</legend>
            <Field label="Hospedagem" htmlFor="asset-hosting">
              <select
                id="asset-hosting"
                className={selectClassName}
                value={draft.location.hosting}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    location: {
                      ...draft.location,
                      hosting: event.target.value as AssetHosting,
                    },
                  })
                }
              >
                {Object.entries(assetHostingLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Provedor ou local" htmlFor="asset-provider">
              <Input
                id="asset-provider"
                required
                value={draft.location.provider}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    location: { ...draft.location, provider: event.target.value },
                  })
                }
                placeholder="Ex.: GitHub Cloud, AWS, Datacenter SP"
              />
            </Field>
            <Field label="Região" htmlFor="asset-region">
              <Input
                id="asset-region"
                required
                value={draft.location.region}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    location: { ...draft.location, region: event.target.value },
                  })
                }
                placeholder="Ex.: sa-east-1 ou Global"
              />
            </Field>
            <Field label="Forma de acesso" htmlFor="asset-access">
              <select
                id="asset-access"
                className={selectClassName}
                value={draft.access}
                onChange={(event) =>
                  setDraft({ ...draft, access: event.target.value as AssetAccess })
                }
              >
                {Object.entries(assetAccessLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
          </fieldset>

          <fieldset className="grid gap-4 sm:grid-cols-2">
            <legend className="label-mono col-span-full mb-1">CONTEXTO DE NEGÓCIO</legend>
            <Field label="Ambiente associado" htmlFor="asset-environment">
              <select
                id="asset-environment"
                className={selectClassName}
                value={draft.environment}
                onChange={(event) =>
                  setDraft({ ...draft, environment: event.target.value as EnvironmentType })
                }
              >
                {Object.entries(environmentLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Criticidade de negócio" htmlFor="asset-criticality">
              <select
                id="asset-criticality"
                className={selectClassName}
                value={draft.businessCriticality ?? ""}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    businessCriticality: (event.target.value || null) as Severity | null,
                  })
                }
              >
                <option value="">Não informada</option>
                {Object.entries(severityLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Classificação dos dados" htmlFor="asset-data">
              <select
                id="asset-data"
                className={selectClassName}
                value={draft.dataClassification}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    dataClassification: event.target.value as AssetDataClassification,
                  })
                }
              >
                {Object.entries(assetDataLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Estado no inventário" htmlFor="asset-status">
              <select
                id="asset-status"
                className={selectClassName}
                value={draft.registryStatus}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    registryStatus: event.target.value as AssetRegistryStatus,
                  })
                }
              >
                {Object.entries(assetStatusLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Tecnologias" htmlFor="asset-technologies" className="sm:col-span-2">
              <Input
                id="asset-technologies"
                value={technologyInput}
                onChange={(event) => setTechnologyInput(event.target.value)}
                placeholder="Ex.: React, TypeScript, AWS"
              />
            </Field>
            <div className="flex items-center justify-between rounded-md border border-border p-3 sm:col-span-2">
              <div>
                <Label htmlFor="asset-real-data">Processa ou armazena dados reais</Label>
                <p className="mt-1 text-xs text-muted-foreground">
                  Não confundir código-fonte confidencial com dados reais de clientes.
                </p>
              </div>
              <select
                id="asset-real-data"
                className={selectClassName}
                value={draft.containsRealData === null ? "unknown" : String(draft.containsRealData)}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    containsRealData:
                      event.target.value === "unknown" ? null : event.target.value === "true",
                  })
                }
              >
                <option value="unknown">Não informado</option>
                <option value="true">Sim</option>
                <option value="false">Não</option>
              </select>
            </div>
          </fieldset>

          {draft.scanMetadata && (
            <details className="rounded border border-border p-3 text-xs">
              <summary>Metadados recebidos na última varredura</summary>
              <p className="mt-2 text-muted-foreground">
                Inclui repositório, branch, commit e APIs consumidas declaradas. Não são serviços
                descobertos automaticamente.
              </p>
              <pre className="mt-3 whitespace-pre-wrap break-all">
                {JSON.stringify(draft.scanMetadata, null, 2)}
              </pre>
            </details>
          )}
          <SheetFooter className="border-t border-border pt-4">
            {saveError ? (
              <p className="mr-auto text-xs text-critical" role="alert">
                {saveError}
              </p>
            ) : null}
            <Button
              type="button"
              variant="outline"
              disabled={saving}
              onClick={() => onOpenChange(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving
                ? "Salvando..."
                : asset?.registryStatus === "pending_review"
                  ? "Confirmar revisão"
                  : asset
                    ? "Salvar configuração"
                    : "Adicionar ativo"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function Field({
  label,
  htmlFor,
  className,
  children,
}: {
  label: string;
  htmlFor: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={className}>
      <Label htmlFor={htmlFor}>{label}</Label>
      <div className="mt-2">{children}</div>
    </div>
  );
}
