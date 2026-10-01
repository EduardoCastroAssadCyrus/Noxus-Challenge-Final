"""Rotas de recebimento para Agent e futura extensão, com chave somente no servidor."""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.routes.local import import_report
from app.core.agent_connection import read_ingestion_key
from app.domain.scan_contract import ScanEnvelope


def require_api_key(request: Request, x_api_key: str | None = Header(None)):
    secret = read_ingestion_key(request.app.state.settings)
    if not secret:
        raise HTTPException(
            503, "Execute bun run agent:init ou configure NOXUS_INGESTION_API_KEY no backend."
        )
    if not x_api_key or not hmac.compare_digest(
        x_api_key.encode(), secret.get_secret_value().encode()
    ):
        raise HTTPException(401, "X-API-Key inválida.")


router = APIRouter(
    prefix="/api", tags=["recebimento-de-varreduras"], dependencies=[Depends(require_api_key)]
)


@router.post("/findings")
async def receive_scan(payload: ScanEnvelope, request: Request):
    return await import_report(payload, request)


@router.post("/integrations/noxus-vscode/scans")
async def receive_extension_scan(payload: ScanEnvelope, request: Request):
    if payload.source != "noxus-vscode-extension":
        raise HTTPException(422, "Esta rota exige source=noxus-vscode-extension.")
    return await import_report(payload, request)


@router.get("/schema")
def schema():
    return ScanEnvelope.model_json_schema()
