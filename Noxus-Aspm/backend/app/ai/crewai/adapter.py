from app.ai.ports import CrewOrchestrator
from app.ai.schemas import (
    CorrelationRequest,
    CorrelationSuggestion,
    RecommendationRequest,
    RecommendationSuggestion,
)
from app.core.errors import IntegrationNotConfiguredError


class CrewAIAdapter(CrewOrchestrator):
    """Único módulo que deverá importar `crewai` quando a integração for autorizada."""

    async def correlate(self, request: CorrelationRequest) -> CorrelationSuggestion:
        del request
        # O agente sugere agrupamentos; o serviço de domínio preserva evidências
        # e exige revisão quando a confiança não for suficiente.
        raise IntegrationNotConfiguredError("CrewAI")

    async def recommend(self, request: RecommendationRequest) -> RecommendationSuggestion:
        del request
        # O agente recebe o score determinístico pronto. Ele explica e recomenda,
        # mas não altera severidade, prioridade ou status diretamente.
        raise IntegrationNotConfiguredError("CrewAI")
