from typing import Protocol

from app.domain.models import (
    Asset,
    AssetCreate,
    AssetUpdate,
    DashboardData,
    Finding,
    Integration,
)


class NoxusRepository(Protocol):
    def dashboard(self) -> DashboardData: ...

    def list_assets(self) -> list[Asset]: ...

    def create_asset(self, payload: AssetCreate) -> Asset: ...

    def update_asset(self, asset_id: str, payload: AssetUpdate) -> Asset | None: ...

    def delete_asset(self, asset_id: str) -> bool: ...

    def list_findings(self) -> list[Finding]: ...

    def get_finding(self, finding_id: str) -> Finding | None: ...

    def list_integrations(self) -> list[Integration]: ...
