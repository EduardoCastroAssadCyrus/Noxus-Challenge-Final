"""API v2 local. Integração da EXTENSÃO NOXUS em /api/integrations/noxus-vscode/scans."""
import hmac
import os
import re
from collections import Counter
from pathlib import Path
from uuid import UUID
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from noxus.models import ScanEnvelope, Triage, NOXUS_VSCODE_EXTENSION_SOURCE
from noxus.storage import JsonStore, Conflict, read_json


def create_app(data_dir=None, api_key=None):
    store = JsonStore(data_dir or os.getenv('NOXUS_DATA_DIR', 'dados'))
    secret = api_key if api_key is not None else os.getenv('NOXUS_API_KEY')
    if not secret:
        raise RuntimeError('Defina NOXUS_API_KEY ou execute python -m noxus serve após init.')
    app = FastAPI(title='NOXUS API', version='2.0.0', description='JSON local + NoxusAgent + futura extensão Noxus VS Code.')
    app.state.store = store

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({'detail': [{'loc': list(e['loc']), 'msg': e['msg'], 'type': e['type']} for e in exc.errors()]}, status_code=422)


    @app.middleware('http')
    async def limit_body(request: Request, call_next):
        if request.method in ('POST', 'PATCH', 'PUT'):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 10 * 1024 * 1024:
                    return JSONResponse({'detail': 'Limite de 10 MiB por requisição.'}, status_code=413)
            request._body = bytes(body)
        try:
            return await call_next(request)
        except TimeoutError:
            return JSONResponse({'detail': 'Armazenamento ocupado; tente novamente.'}, status_code=503)

    def auth(x_api_key: str | None = Header(None)):
        if not x_api_key or not hmac.compare_digest(x_api_key, secret):
            raise HTTPException(401, 'X-API-Key inválida.')
    deps = [Depends(auth)]

    @app.get('/health')
    def health():
        return {'status': 'ok', 'storage': 'json', 'version': '2.0.0'}

    def ingest(payload):
        try:
            return store.ingest(payload)
        except Conflict as e:
            raise HTTPException(409, str(e))

    @app.post('/api/findings', dependencies=deps, tags=['Ingestão'])
    def receive_agent_or_extension(payload: ScanEnvelope):
        return ingest(payload)

    # EXTENSÃO NOXUS (SonarQube for IDE modificado): rota dedicada para o futuro fork.
    # A extensão ainda não existe neste pacote. Deve enviar o contrato ScanEnvelope.
    # source identifica o produtor; scan.tool identifica sonar/dependency-reputation/etc.
    @app.post('/api/integrations/noxus-vscode/scans', dependencies=deps, tags=['EXTENSÃO NOXUS VS CODE'])
    def receive_noxus_vscode_extension_scan(payload: ScanEnvelope):
        if payload.source != NOXUS_VSCODE_EXTENSION_SOURCE:
            raise HTTPException(422, 'Esta rota é exclusiva da EXTENSÃO NOXUS: source=noxus-vscode-extension.')
        return ingest(payload)

    @app.get('/api/schema', dependencies=deps)
    def schema():
        return ScanEnvelope.model_json_schema()

    @app.get('/api/scans', dependencies=deps)
    def scans(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        records = store.scan_list()[::-1]
        items = [{'received_at': r['received_at'], 'source': r['payload']['source'],
                  'asset': r['payload']['asset'], 'scan': r['payload']['scan'],
                  'findings_count': len(r['payload']['findings'])} for r in records]
        return {'total': len(items), 'items': items[offset:offset+limit]}

    @app.get('/api/scans/{scan_id}', dependencies=deps)
    def scan(scan_id: UUID):
        p = store.scans / (str(scan_id) + '.json')
        if not p.exists():
            raise HTTPException(404, 'Varredura não encontrada.')
        return read_json(p)

    @app.get('/api/findings', dependencies=deps)
    def findings(asset_id: str | None = None, source: str | None = None, tool: str | None = None,
                 severity: str | None = None, status: str | None = None,
                 limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        filters = {'asset_id': asset_id, 'source': source, 'tool': tool, 'severity': severity, 'status': status}
        rows = [r for r in store.findings() if all(v is None or r[k] == v for k,v in filters.items())]
        return {'total': len(rows), 'items': rows[offset:offset+limit]}

    def valid_id(key):
        if not re.fullmatch('[0-9a-f]{64}', key):
            raise HTTPException(422, 'ID inválido.')

    @app.patch('/api/findings/{finding_id}/status', dependencies=deps)
    def triage(finding_id: str, change: Triage):
        valid_id(finding_id)
        try:
            return store.triage(finding_id, change)
        except KeyError:
            raise HTTPException(404, 'Finding não encontrado.')

    @app.get('/api/findings/{finding_id}/history', dependencies=deps)
    def history(finding_id: str):
        valid_id(finding_id)
        if not any(x['id'] == finding_id for x in store.findings()):
            raise HTTPException(404, 'Finding não encontrado.')
        p = store.root / 'triage' / (finding_id + '.json')
        return read_json(p) if p.exists() else {'history': []}

    @app.get('/api/assets', dependencies=deps)
    def assets():
        result = {}
        for r in store.scan_list():
            a = r['payload']['asset']; result[a['id']] = a
        return {'total': len(result), 'items': list(result.values())}

    @app.get('/api/dashboard', dependencies=deps)
    def dashboard():
        rows = store.findings()
        return {'total_scans': len(store.scan_list()), 'total_findings': len(rows),
                'total_assets': assets()['total'], 'by_severity': dict(Counter(r['severity'] or 'unknown' for r in rows)),
                'by_status': dict(Counter(r['status'] for r in rows)), 'by_source': dict(Counter(r['source'] for r in rows))}
    return app
