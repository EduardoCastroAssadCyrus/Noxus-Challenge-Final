from fastapi import APIRouter, Request

from app.domain.models import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/api/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    repository = request.app.state.repository
    return HealthResponse(
        status="ok",
        service="noxus-aspm-api",
        environment=settings.environment,
        data_store=repository.name,
        chat_provider=settings.chat_provider,
        crew_provider=settings.crew_provider,
    )
