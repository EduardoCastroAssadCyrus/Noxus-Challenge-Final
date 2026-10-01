from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base comum: Python usa snake_case e a API preserva o camelCase do React."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScannerSource(StrEnum):
    EXTENSION = "EXTENSION"
    SAST = "SAST"
    DAST = "DAST"
    SCA = "SCA"
    SECRET = "SECRET"
    GUARDRAIL = "GUARDRAIL"


class EnvironmentType(StrEnum):
    UNKNOWN = "unknown"
    PRODUCTION = "production"
    STAGING = "staging"
    TEST = "test"
    DEVELOPMENT = "development"
    SHARED = "shared"


class AssetType(StrEnum):
    APPLICATION = "application"
    REPOSITORY = "repository"
    API = "api"
    SERVICE = "service"
    DATABASE = "database"
    CONTAINER = "container"


class AssetAccess(StrEnum):
    UNKNOWN = "unknown"
    PUBLIC_INTERNET = "public_internet"
    RESTRICTED_INTERNET = "restricted_internet"
    PRIVATE_NETWORK = "private_network"


class AssetHosting(StrEnum):
    UNKNOWN = "unknown"
    SAAS = "saas"
    PUBLIC_CLOUD = "public_cloud"
    PRIVATE_CLOUD = "private_cloud"
    ON_PREMISES = "on_premises"


class AssetDataClassification(StrEnum):
    UNKNOWN = "unknown"
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AssetRegistrationSource(StrEnum):
    MANUAL = "manual"
    AI_DISCOVERY = "ai_discovery"
    INTEGRATION = "integration"


class AssetRegistryStatus(StrEnum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    INACTIVE = "inactive"


class AssetLocation(ApiModel):
    hosting: AssetHosting
    provider: str = Field(min_length=1, max_length=120)
    region: str = Field(min_length=1, max_length=120)


class Asset(ApiModel):
    id: str
    name: str
    application_name: str
    type: AssetType
    identifier: str
    repo: str
    environment: EnvironmentType
    owner: str
    business_criticality: Severity | None
    access: AssetAccess
    location: AssetLocation
    data_classification: AssetDataClassification
    contains_real_data: bool | None
    scan_metadata: dict | None = None
    technologies: list[str]
    registration_source: AssetRegistrationSource
    registry_status: AssetRegistryStatus
    discovery_confidence: float | None = Field(default=None, ge=0, le=1)
    assessment_status: Literal["assessed", "not_assessed"]
    risk_score: int | None = Field(default=None, ge=0, le=100)
    open_findings: int = Field(ge=0)
    last_scan_at: datetime | None = None
    last_seen_at: datetime
    compliance: int | None = Field(default=None, ge=0, le=100)


class AssetCreate(ApiModel):
    """Somente campos que o cliente pode informar ao cadastrar um ativo."""

    name: str = Field(min_length=2, max_length=160)
    application_name: str = Field(min_length=2, max_length=160)
    type: AssetType
    identifier: str = Field(min_length=2, max_length=500)
    repo: str = Field(default="", max_length=300)
    environment: EnvironmentType
    owner: str = Field(min_length=2, max_length=160)
    business_criticality: Severity | None
    access: AssetAccess
    location: AssetLocation
    data_classification: AssetDataClassification
    contains_real_data: bool | None = None
    technologies: list[str] = Field(default_factory=list, max_length=40)
    registration_source: AssetRegistrationSource = AssetRegistrationSource.MANUAL
    registry_status: AssetRegistryStatus = AssetRegistryStatus.ACTIVE
    discovery_confidence: float | None = Field(default=None, ge=0, le=1)


class AssetUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    application_name: str | None = Field(default=None, min_length=2, max_length=160)
    type: AssetType | None = None
    identifier: str | None = Field(default=None, min_length=2, max_length=500)
    repo: str | None = Field(default=None, max_length=300)
    environment: EnvironmentType | None = None
    owner: str | None = Field(default=None, min_length=2, max_length=160)
    business_criticality: Severity | None = None
    access: AssetAccess | None = None
    location: AssetLocation | None = None
    data_classification: AssetDataClassification | None = None
    contains_real_data: bool | None = None
    technologies: list[str] | None = Field(default=None, max_length=40)
    registry_status: AssetRegistryStatus | None = None


class FindingStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    NEEDS_REVIEW = "needs_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class CorrelationStatus(StrEnum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    UNMATCHED = "unmatched"


class FindingEvidence(ApiModel):
    source: ScannerSource
    tool: str
    source_finding_id: str


class Finding(ApiModel):
    id: str
    title: str
    asset_id: str | None = None
    asset_name: str | None = None
    source: ScannerSource
    tool: str
    technical_severity: Severity | None
    producer: str | None = None
    scan_id: str | None = None
    occurrences: int = 1
    operational_priority: Severity | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    priority_explanation: str
    status: FindingStatus
    cve: str | None = None
    file: str | None = None
    line: int | None = Field(default=None, ge=1)
    detected_at: datetime | None = None
    correlated_count: int = Field(ge=0)
    correlation_status: CorrelationStatus
    correlation_confidence: float = Field(ge=0, le=1)
    evidences: list[FindingEvidence]
    description: str
    remediation: str
    original: dict = Field(default_factory=dict)
    imported_at: datetime | None = None
    analysis: "FindingAnalysis | None" = None


class FindingAnalysis(ApiModel):
    classification: Literal["true_positive", "false_positive", "inconclusive"]
    confidence: float = Field(ge=0, le=1)
    reason: str
    evidence: list[str]
    run_id: str
    analyzed_at: datetime


class AnalysisRun(ApiModel):
    id: str
    status: Literal["queued", "running", "completed", "failed", "interrupted"]
    finding_ids: list[str]
    created_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
    stage: str | None = None


class RunRequest(ApiModel):
    finding_ids: list[str] = Field(default_factory=list, max_length=50)


class LocalState(ApiModel):
    schema_version: Literal[1] = 1
    assets: list[Asset] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    runs: list[AnalysisRun] = Field(default_factory=list)
    processed_scan_ids: list[str] = Field(default_factory=list)


class AgentId(StrEnum):
    FEEDBACK = "feedback"
    CHATBOT = "chatbot"
    CORRELATION = "correlation"
    REMEDIATION = "remediation"
    EMERGENCY = "emergency"


class AgentStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DEGRADED = "degraded"


class Agent(ApiModel):
    id: AgentId
    name: str
    role: str
    status: AgentStatus
    tasks_today: int = Field(ge=0)
    last_action: str
    last_action_at: datetime
    throughput: int = Field(ge=0, le=100)


class MetricSummary(ApiModel):
    open_findings: int = Field(ge=0)
    open_findings_delta: int | None = None
    critical_findings: int = Field(ge=0)
    alerts_reviewed: int = Field(ge=0)
    correlation_rate: float = Field(ge=0, le=1)
    mean_time_to_remediate: int | None = Field(default=None, ge=0)
    monitored_assets: int = Field(ge=0)
    secrets_blocked: int | None = Field(default=None, ge=0)
    guardrail_blocks: int | None = Field(default=None, ge=0)
    compliance_score: int | None = Field(default=None, ge=0, le=100)
    true_positives: int = 0
    false_positives: int = 0
    inconclusive: int = 0
    pending_analysis: int = 0


class TrendPoint(ApiModel):
    date: date
    critical: int = Field(ge=0)
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)
    info: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)


class SourceBreakdown(ApiModel):
    source: ScannerSource
    findings: int = Field(ge=0)
    reviewed: int = Field(ge=0)


class EmergencyAlert(ApiModel):
    id: str
    title: str
    detail: str
    severity: Severity
    asset_name: str
    created_at: datetime
    acknowledged: bool


class IntegrationStatus(StrEnum):
    READY_TO_CONNECT = "ready_to_connect"
    PLANNED = "planned"


class IntegrationCategory(StrEnum):
    SCANNER = "scanner"
    ORCHESTRATION = "orchestration"
    AI = "ai"
    DEVELOPER = "developer"


class Integration(ApiModel):
    id: str
    name: str
    category: IntegrationCategory
    role: str
    transport: str
    expected_format: str
    status: IntegrationStatus


class DashboardData(ApiModel):
    metrics: MetricSummary
    assets: list[Asset]
    findings: list[Finding]
    agents: list[Agent]
    trend: list[TrendPoint]
    sources: list[SourceBreakdown]
    alerts: list[EmergencyAlert]
    integrations: list[Integration]


class ChatRequest(ApiModel):
    content: str = Field(min_length=1, max_length=8_000)
    finding_id: str | None = None
    application_id: str | None = None


class ChatMessage(ApiModel):
    id: str
    role: Literal["assistant"] = "assistant"
    content: str
    created_at: datetime


class HealthResponse(ApiModel):
    status: str
    service: str
    environment: str
    data_store: str
    chat_provider: str
    crew_provider: str
