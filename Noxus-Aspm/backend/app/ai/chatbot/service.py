from datetime import UTC, datetime
from uuid import uuid4

from app.ai.ports import ChatProvider
from app.ai.schemas import AuthorizedChatContext
from app.domain.models import ChatMessage, ChatRequest, Finding


class ChatService:
    def __init__(self, provider: ChatProvider) -> None:
        self._provider = provider

    async def reply(self, request: ChatRequest, finding: Finding | None) -> ChatMessage:
        # Antes de habilitar IA, inclua aqui autenticação, autorização por tenant,
        # filtragem de evidências e o registro auditável da execução.
        result = await self._provider.reply(
            AuthorizedChatContext(
                message=request.content,
                finding=finding,
                application_id=request.application_id,
            )
        )
        return ChatMessage(
            id=f"msg-{uuid4().hex[:12]}",
            content=result.content,
            created_at=datetime.now(UTC),
        )
