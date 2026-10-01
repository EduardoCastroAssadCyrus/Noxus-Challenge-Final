from typing import cast

from fastapi import Request

from app.ai.chatbot.service import ChatService
from app.repositories.contracts import NoxusRepository


def get_repository(request: Request) -> NoxusRepository:
    return cast(NoxusRepository, request.app.state.repository)


def get_chat_service(request: Request) -> ChatService:
    return cast(ChatService, request.app.state.chat_service)
