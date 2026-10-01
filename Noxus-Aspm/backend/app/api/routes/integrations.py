from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_repository
from app.domain.models import Integration
from app.repositories.contracts import NoxusRepository

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[Integration])
def list_integrations(
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> list[Integration]:
    return repository.list_integrations()
