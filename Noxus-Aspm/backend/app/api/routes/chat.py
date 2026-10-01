from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.chatbot.service import ChatService
from app.core.errors import IntegrationNotConfiguredError
from app.dependencies import get_chat_service, get_repository
from app.domain.models import ChatMessage, ChatRequest
from app.repositories.contracts import NoxusRepository

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatMessage)
async def send_message(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> ChatMessage:
    finding = repository.get_finding(payload.finding_id) if payload.finding_id else None
    try:
        return await service.reply(payload, finding)
    except IntegrationNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "chat_provider_not_configured", "message": str(error)},
        ) from error
