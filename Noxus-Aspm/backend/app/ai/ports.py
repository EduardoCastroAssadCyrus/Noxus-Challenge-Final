from typing import Protocol

from app.ai.schemas import (
    AuthorizedChatContext,
    ChatProviderResult,
    CorrelationRequest,
    CorrelationSuggestion,
    RecommendationRequest,
    RecommendationSuggestion,
)


class ChatProvider(Protocol):
    async def reply(self, context: AuthorizedChatContext) -> ChatProviderResult: ...


class CrewOrchestrator(Protocol):
    async def correlate(self, request: CorrelationRequest) -> CorrelationSuggestion: ...

    async def recommend(self, request: RecommendationRequest) -> RecommendationSuggestion: ...
