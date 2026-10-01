from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_repository
from app.domain.models import Finding
from app.repositories.contracts import NoxusRepository

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=list[Finding])
def list_findings(
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> list[Finding]:
    return repository.list_findings()


@router.get("/{finding_id}", response_model=Finding)
def get_finding(
    finding_id: str,
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> Finding:
    finding = repository.get_finding(finding_id)
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "finding_not_found", "message": "Finding não encontrado."},
        )
    return finding
