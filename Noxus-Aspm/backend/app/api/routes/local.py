from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.domain.models import AnalysisRun, RunRequest
from app.domain.scan_contract import ScanEnvelope
from app.ingestion import digest

router = APIRouter(tags=["fluxo-local"])


class ClearReportsRequest(BaseModel):
    confirmation: Literal["LIMPAR DADOS"]


@router.post("/reports/clear")
def clear_reports(payload: ClearReportsRequest, request: Request):
    # Recurso temporário para o protótipo local, desabilitado em produção.
    if request.app.state.settings.environment not in {"development", "test"}:
        raise HTTPException(403, "Limpeza disponível somente no ambiente de testes local.")
    try:
        return request.app.state.repository.clear_reports()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/imports", status_code=201)
async def import_report(payload: ScanEnvelope, request: Request):
    try:
        # Guardamos somente um resumo criptográfico do conteúdo recebido, nunca o SECRET bruto.
        return request.app.state.repository.ingest_scan(payload, digest(await request.json()))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/scans")
def list_scans(request: Request):
    return request.app.state.repository.list_scans()


@router.get("/analysis/status")
def analysis_status(request: Request):
    return request.app.state.crew_runner.availability()


@router.get("/analysis/runs", response_model=list[AnalysisRun])
def list_runs(request: Request):
    return request.app.state.crew_runner.runs()


@router.post("/analysis/runs", response_model=AnalysisRun, status_code=202)
def start_run(payload: RunRequest, request: Request):
    runner = request.app.state.crew_runner
    availability = runner.availability(refresh=True)
    if not availability["ready"]:
        raise HTTPException(503, availability.get("error") or "CrewAI não configurado.")
    try:
        run, findings = request.app.state.repository.create_run(payload.finding_ids)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    runner.submit(run, findings)
    return run
