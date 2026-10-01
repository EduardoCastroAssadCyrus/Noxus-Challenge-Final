from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_repository
from app.domain.models import DashboardData
from app.repositories.contracts import NoxusRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardData)
def get_dashboard(
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> DashboardData:
    return repository.dashboard()
