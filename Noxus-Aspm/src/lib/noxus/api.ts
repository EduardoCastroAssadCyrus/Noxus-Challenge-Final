import { queryOptions } from "@tanstack/react-query";

import { createHttpGateway } from "./http-gateway";
import { noxusRuntimeConfig } from "./runtime-config";
import type {
  Asset,
  AssetUpdateRequest,
  AssetWriteRequest,
  ChatRequest,
  ScanEnvelopeInput,
} from "./types";

/**
 * Este é o ponto de acesso do front-end à API local.
 * Não faça chamadas HTTP diretamente nas páginas; adicione operações ao gateway.
 */
const gateway = createHttpGateway(noxusRuntimeConfig.apiBaseUrl);

export const dataSource = noxusRuntimeConfig.dataSource;
export const clearReports = () => gateway.clearReports();

export const fetchDashboard = (signal?: AbortSignal) => gateway.getDashboard(signal);

export const fetchFinding = (id: string, signal?: AbortSignal) => gateway.getFinding(id, signal);

export const createAsset = (request: AssetWriteRequest) => gateway.createAsset(request);

export const updateAsset = (id: string, request: AssetUpdateRequest) =>
  gateway.updateAsset(id, request);

export const toAssetWriteRequest = (asset: Asset): AssetWriteRequest => ({
  name: asset.name,
  applicationName: asset.applicationName,
  type: asset.type,
  identifier: asset.identifier,
  repo: asset.repo,
  environment: asset.environment,
  owner: asset.owner,
  businessCriticality: asset.businessCriticality,
  access: asset.access,
  location: asset.location,
  dataClassification: asset.dataClassification,
  containsRealData: asset.containsRealData,
  technologies: asset.technologies,
  registrationSource: asset.registrationSource,
  registryStatus: asset.registryStatus,
  discoveryConfidence: asset.discoveryConfidence,
});

export const toAssetUpdateRequest = (asset: Asset): AssetUpdateRequest => {
  const {
    registrationSource: _source,
    discoveryConfidence: _confidence,
    ...request
  } = toAssetWriteRequest(asset);
  return request;
};

export const sendChatMessage = (request: ChatRequest) => gateway.sendChatMessage(request);
export const importFindings = (request: ScanEnvelopeInput) => gateway.importFindings(request);
export const scansQuery = queryOptions({
  queryKey: ["noxus", "scans"],
  queryFn: ({ signal }) => gateway.listScans(signal),
  refetchInterval: 5_000,
});
export const startAnalysis = (findingIds: string[] = []) => gateway.startAnalysis(findingIds);
export const analysisStatusQuery = queryOptions({
  queryKey: ["noxus", "analysis-status"],
  queryFn: ({ signal }) => gateway.analysisStatus(signal),
  refetchInterval: 15_000,
});
export const analysisRunsQuery = queryOptions({
  queryKey: ["noxus", "analysis-runs"],
  queryFn: ({ signal }) => gateway.analysisRuns(signal),
  refetchInterval: 2_000,
});

export const dashboardQuery = queryOptions({
  queryKey: ["noxus", "dashboard", dataSource],
  queryFn: ({ signal }) => fetchDashboard(signal),
  refetchInterval: 3_000,
  staleTime: 30_000,
});

export const assetsQuery = queryOptions({
  queryKey: ["noxus", "assets", dataSource],
  queryFn: ({ signal }) => gateway.listAssets(signal),
  staleTime: 30_000,
});

export const findingsQuery = queryOptions({
  queryKey: ["noxus", "findings", dataSource],
  queryFn: ({ signal }) => gateway.listFindings(signal),
  refetchInterval: 3_000,
  staleTime: 30_000,
});

export const integrationsQuery = queryOptions({
  queryKey: ["noxus", "integrations", dataSource],
  queryFn: ({ signal }) => gateway.listIntegrations(signal),
  staleTime: 30_000,
});

export const findingQuery = (id: string) =>
  queryOptions({
    queryKey: ["noxus", "finding", id, dataSource],
    queryFn: ({ signal }) => fetchFinding(id, signal),
  });
