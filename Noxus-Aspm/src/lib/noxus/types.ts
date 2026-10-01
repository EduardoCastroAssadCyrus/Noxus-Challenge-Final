/**
 * Contratos compartilhados pelo front-end do Noxus.
 *
 * Esses formatos são preenchidos pela API local. O backend mantém os contratos
 * para que as telas não precisem
 * conhecer FastAPI, CrewAI, filas ou o formato particular de cada scanner.
 */

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type ScannerSource = "SAST" | "DAST" | "SCA" | "SECRET" | "EXTENSION" | "GUARDRAIL";

export type FindingStatus =
  "open" | "triaged" | "needs_review" | "in_progress" | "resolved" | "false_positive";

export type EnvironmentType =
  "production" | "staging" | "test" | "development" | "shared" | "unknown";

export type AssetType = "repository" | "api" | "service" | "database" | "container" | "application";

export type AssetAccess = "public_internet" | "restricted_internet" | "private_network" | "unknown";

export type AssetHosting = "saas" | "public_cloud" | "private_cloud" | "on_premises" | "unknown";

export type AssetDataClassification =
  "public" | "internal" | "confidential" | "restricted" | "unknown";

export type AssetRegistrationSource = "manual" | "ai_discovery" | "integration";

export type AssetRegistryStatus = "active" | "pending_review" | "inactive";

export interface AssetLocation {
  hosting: AssetHosting;
  provider: string;
  region: string;
}

export interface Asset {
  id: string;
  name: string;
  applicationName: string;
  type: AssetType;
  identifier: string;
  repo: string;
  environment: EnvironmentType;
  owner: string;
  businessCriticality: Severity | null;
  access: AssetAccess;
  location: AssetLocation;
  dataClassification: AssetDataClassification;
  containsRealData: boolean | null;
  scanMetadata?: Record<string, unknown> | null;
  technologies: string[];
  registrationSource: AssetRegistrationSource;
  registryStatus: AssetRegistryStatus;
  discoveryConfidence: number | null; // 0-1; preenchido apenas pela descoberta assistida
  assessmentStatus: "assessed" | "not_assessed";
  riskScore: number | null;
  openFindings: number;
  lastScanAt: string | null; // ISO; nulo enquanto nenhum scanner avaliou o ativo
  lastSeenAt: string; // ISO; última confirmação do ativo no inventário
  compliance: number | null;
}

/** Campos editáveis enviados ao backend; score, datas e contagens pertencem ao servidor. */
export type AssetWriteRequest = Pick<
  Asset,
  | "name"
  | "applicationName"
  | "type"
  | "identifier"
  | "repo"
  | "environment"
  | "owner"
  | "businessCriticality"
  | "access"
  | "location"
  | "dataClassification"
  | "containsRealData"
  | "technologies"
  | "registrationSource"
  | "registryStatus"
  | "discoveryConfidence"
>;

export type AssetUpdateRequest = Omit<
  AssetWriteRequest,
  "registrationSource" | "discoveryConfidence"
>;

export interface Finding {
  id: string;
  title: string;
  assetId?: string;
  assetName?: string;
  source: ScannerSource;
  tool: string;
  technicalSeverity: Severity | null;
  producer?: string | null;
  scanId?: string | null;
  occurrences: number;
  operationalPriority: Severity | null;
  riskScore: number | null;
  priorityExplanation: string;
  status: FindingStatus;
  cve?: string;
  file?: string;
  line?: number;
  detectedAt: string | null; // data informada pelo scanner, quando disponível
  correlatedCount: number;
  correlationStatus: "matched" | "needs_review" | "unmatched";
  correlationConfidence: number; // 0-1
  evidences: FindingEvidence[];
  description: string;
  remediation: string;
  original: Record<string, unknown>;
  importedAt?: string;
  analysis?: FindingAnalysis | null;
}

export interface FindingAnalysis {
  classification: "true_positive" | "false_positive" | "inconclusive";
  confidence: number;
  reason: string;
  evidence: string[];
  runId: string;
  analyzedAt: string;
}

export interface AnalysisRun {
  id: string;
  status: "queued" | "running" | "completed" | "failed" | "interrupted";
  findingIds: string[];
  createdAt: string;
  finishedAt: string | null;
  error: string | null;
  stage: string | null;
}

export interface AnalysisStatus {
  ready: boolean;
  provider: string | null;
  error: string | null;
}

export interface FindingEvidence {
  source: ScannerSource;
  tool: string;
  sourceFindingId: string;
}

export type AgentId = "feedback" | "chatbot" | "correlation" | "remediation" | "emergency";

export interface Agent {
  id: AgentId;
  name: string;
  role: string;
  status: "idle" | "running" | "degraded";
  tasksToday: number;
  lastAction: string;
  lastActionAt: string; // ISO
  throughput: number;
}

export interface MetricSummary {
  truePositives: number;
  falsePositives: number;
  inconclusive: number;
  pendingAnalysis: number;
  openFindings: number;
  openFindingsDelta: number | null;
  criticalFindings: number;
  alertsReviewed: number;
  correlationRate: number; // 0-1
  meanTimeToRemediate: number | null;
  monitoredAssets: number;
  secretsBlocked: number | null;
  guardrailBlocks: number | null;
  complianceScore: number | null;
}

export interface TrendPoint {
  date: string; // ISO date
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  unknown: number;
}

/** Envelope enviado inteiro; a validação autoritativa do contrato fica no backend. */
export type ScanEnvelopeInput = Record<string, unknown>;

export interface ScanImportResult {
  scan_id: string;
  received: number;
  replayed: boolean;
  created: number;
  updated: number;
  duplicates: number;
}

export interface ScanSummary {
  received_at: string;
  source: string;
  asset: { id: string; name: string };
  scan: {
    id: string;
    tool: string;
    status: "completed" | "partial" | "failed";
    finished_at: string;
    error: string | null;
  };
  findings_count: number;
}

export interface SourceBreakdown {
  source: ScannerSource;
  findings: number;
  reviewed: number;
}

export interface EmergencyAlert {
  id: string;
  title: string;
  detail: string;
  severity: Severity;
  assetName: string;
  createdAt: string;
  acknowledged: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export interface ChatRequest {
  content: string;
  findingId?: string;
  applicationId?: string;
}

export type IntegrationStatus = "ready_to_connect" | "planned";

export interface Integration {
  id: string;
  name: string;
  category: "scanner" | "orchestration" | "ai" | "developer";
  role: string;
  transport: string;
  expectedFormat: string;
  status: IntegrationStatus;
}

export interface DashboardData {
  metrics: MetricSummary;
  assets: Asset[];
  findings: Finding[];
  agents: Agent[];
  trend: TrendPoint[];
  sources: SourceBreakdown[];
  alerts: EmergencyAlert[];
  integrations: Integration[];
}
