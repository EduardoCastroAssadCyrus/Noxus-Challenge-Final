from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.errors import DuplicateAssetIdentifierError
from app.dependencies import get_repository
from app.domain.models import Asset, AssetCreate, AssetUpdate
from app.repositories.contracts import NoxusRepository

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[Asset])
def list_assets(repository: Annotated[NoxusRepository, Depends(get_repository)]) -> list[Asset]:
    return repository.list_assets()


@router.post(
    "",
    response_model=Asset,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    payload: AssetCreate,
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> Asset:
    try:
        return repository.create_asset(payload)
    except DuplicateAssetIdentifierError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_asset_identifier", "message": str(error)},
        ) from error


@router.patch("/{asset_id}", response_model=Asset)
def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> Asset:
    try:
        asset = repository.update_asset(asset_id, payload)
    except DuplicateAssetIdentifierError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_asset_identifier", "message": str(error)},
        ) from error

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "asset_not_found", "message": "Ativo não encontrado."},
        )
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    repository: Annotated[NoxusRepository, Depends(get_repository)],
) -> None:
    if not repository.delete_asset(asset_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "asset_not_found", "message": "Ativo não encontrado."},
        )
