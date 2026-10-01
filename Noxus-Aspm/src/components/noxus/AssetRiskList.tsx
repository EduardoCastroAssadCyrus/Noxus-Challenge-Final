import { severityBar } from "@/lib/noxus/ui";
import { relativeTime } from "@/lib/noxus/ui";
import type { Asset } from "@/lib/noxus/types";
import { environmentLabel } from "@/lib/noxus/asset-labels";

export function AssetRiskList({ assets }: { assets: Asset[] }) {
  return (
    <div className="panel min-w-0 p-4">
      <p className="label-mono">Ativos cadastrados</p>
      {assets.length === 0 && (
        <p className="mt-4 text-sm text-muted-foreground">Nenhum ativo cadastrado.</p>
      )}
      <ul className="mt-4 flex flex-col gap-4">
        {assets.map((asset) => (
          <li key={asset.id}>
            <div className="flex items-baseline justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{asset.name}</p>
                <p className="truncate font-mono text-xs text-muted-foreground">
                  {asset.repo} · {environmentLabel[asset.environment]}
                </p>
              </div>
              <span className="font-mono text-sm">{asset.riskScore ?? "—"}</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full rounded-full ${asset.businessCriticality ? severityBar[asset.businessCriticality] : "bg-muted"}`}
                style={{ width: `${asset.riskScore ?? 0}%` }}
                role="progressbar"
                aria-label={`Risco de ${asset.name}`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={asset.riskScore ?? undefined}
              />
            </div>
            <p className="mt-1.5 flex justify-between text-xs text-muted-foreground">
              <span>{asset.openFindings} achados abertos</span>
              <span>
                scan {asset.lastScanAt ? relativeTime(asset.lastScanAt) : "não realizado"}
              </span>
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
