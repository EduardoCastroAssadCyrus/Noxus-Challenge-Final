from pydantic import Field

from app.domain.models import ApiModel, Finding


class AuthorizedChatContext(ApiModel):
    """Contexto já autenticado e filtrado antes de chegar ao provedor de IA."""

    message: str = Field(min_length=1, max_length=8_000)
    finding: Finding | None = None
    application_id: str | None = None
    organization_id: str | None = None


class ChatProviderResult(ApiModel):
    content: str
    references: list[str] = Field(default_factory=list)
    model: str
    prompt_version: str


class CorrelationRequest(ApiModel):
    finding_ids: list[str]
    organization_id: str


class CorrelationSuggestion(ApiModel):
    finding_ids: list[str]
    explanation: str
    confidence: float = Field(ge=0, le=1)


class RecommendationRequest(ApiModel):
    finding_id: str
    organization_id: str


class RecommendationSuggestion(ApiModel):
    finding_id: str
    guidance: str
    facts_used: list[str]
    confidence: float = Field(ge=0, le=1)
