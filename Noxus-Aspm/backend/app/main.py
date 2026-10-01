from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.chatbot.service import ChatService
from app.ai.disabled import DisabledChatProvider
from app.ai.local_runner import LocalCrewRunner
from app.api.router import api_router
from app.api.routes.local import router as local_router
from app.api.routes.scan_ingestion import router as scan_router
from app.api.routes.system import router as system_router
from app.core.config import Settings, get_settings
from app.core.local_lock import local_store_lock
from app.repositories.json_repository import JsonNoxusRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    current_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application):
        with local_store_lock(current_settings.resolved_data_file):
            repository = JsonNoxusRepository(current_settings.resolved_data_file)
            repository.recover_interrupted()
            runner = LocalCrewRunner(current_settings, repository)
            application.state.repository = repository
            application.state.crew_runner = runner
            try:
                yield
            finally:
                runner.close()

    application = FastAPI(
        title="Noxus ASPM API",
        version="0.1.0",
        lifespan=lifespan,
        description=(
            "Fluxo local com arquivos JSON, importação de findings e triagem pelo Challenge3."
        ),
    )
    application.state.settings = current_settings
    application.state.chat_service = ChatService(DisabledChatProvider())

    @application.exception_handler(RequestValidationError)
    async def safe_validation_error(request, exc):
        # Pydantic inclui o input no erro padrão: isso poderia devolver segredos ao navegador.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
                    for error in exc.errors()
                ]
            },
        )

    @application.middleware("http")
    async def limit_body(request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 10 * 1024 * 1024:
                    return JSONResponse(
                        status_code=413, content={"detail": "Limite de 10 MiB por requisição."}
                    )
                body.extend(chunk)
            request._body = bytes(body)
        return await call_next(request)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type", "X-API-Key"],
    )

    application.include_router(system_router)
    application.include_router(api_router, prefix=current_settings.api_prefix)
    application.include_router(local_router, prefix=current_settings.api_prefix)
    application.include_router(scan_router)
    return application


app = create_app()
