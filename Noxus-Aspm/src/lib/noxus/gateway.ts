import type {
  Asset,
  AssetUpdateRequest,
  AssetWriteRequest,
  ChatMessage,
  ChatRequest,
  DashboardData,
  Finding,
  Integration,
  AnalysisRun,
  AnalysisStatus,
  ScanEnvelopeInput,
  ScanImportResult,
  ScanSummary,
} from "./types";

/**
 * Porta de entrada dos dados usados pela interface.
 *
 * O adaptador HTTP implementa esta interface. Assim,
 * componentes React não precisam saber de onde os dados vieram.
 */
export interface NoxusGateway {
  clearReports(): Promise<{ findings: number; scans: number; runs: number }>;
  importFindings(request: ScanEnvelopeInput): Promise<ScanImportResult>;
  listScans(signal?: AbortSignal): Promise<ScanSummary[]>;
  startAnalysis(findingIds: string[]): Promise<AnalysisRun>;
  analysisStatus(signal?: AbortSignal): Promise<AnalysisStatus>;
  analysisRuns(signal?: AbortSignal): Promise<AnalysisRun[]>;
  getDashboard(signal?: AbortSignal): Promise<DashboardData>;
  listAssets(signal?: AbortSignal): Promise<Asset[]>;
  createAsset(request: AssetWriteRequest): Promise<Asset>;
  updateAsset(id: string, request: AssetUpdateRequest): Promise<Asset>;
  listFindings(signal?: AbortSignal): Promise<Finding[]>;
  listIntegrations(signal?: AbortSignal): Promise<Integration[]>;
  getFinding(id: string, signal?: AbortSignal): Promise<Finding | undefined>;
  sendChatMessage(request: ChatRequest): Promise<ChatMessage>;
}
