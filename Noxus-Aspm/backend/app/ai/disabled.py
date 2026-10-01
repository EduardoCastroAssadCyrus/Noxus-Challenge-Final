from app.ai.ports import ChatProvider, CrewOrchestrator
from app.ai.schemas import (
    AuthorizedChatContext,
    ChatProviderResult,
    CorrelationRequest,
    CorrelationSuggestion,
    RecommendationRequest,
    RecommendationSuggestion,
)
from app.core.errors import IntegrationNotConfiguredError


class DisabledChatProvider(ChatProvider):
    async def reply(self, context: AuthorizedChatContext) -> ChatProviderResult:
        del context
        raise IntegrationNotConfiguredError("chatbot")


class DisabledCrewOrchestrator(CrewOrchestrator):
    async def correlate(self, request: CorrelationRequest) -> CorrelationSuggestion:
        del request
        raise IntegrationNotConfiguredError("CrewAI")

    async def recommend(self, request: RecommendationRequest) -> RecommendationSuggestion:
        del request
        raise IntegrationNotConfiguredError("CrewAI")
