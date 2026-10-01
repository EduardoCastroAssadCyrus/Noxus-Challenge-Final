import json
import os
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.core.errors import DuplicateAssetIdentifierError
from app.domain.models import (
    AnalysisRun,
    Asset,
    AssetCreate,
    AssetUpdate,
    DashboardData,
    FindingAnalysis,
    LocalState,
    MetricSummary,
    SourceBreakdown,
    TrendPoint,
)
from app.domain.scan_contract import ScanEnvelope
from app.ingestion import imported_asset, normalize


class JsonNoxusRepository:
    """Um processo local escreve o JSON. Toda alteração passa pelo mesmo bloqueio."""

    def __init__(self, data_file: Path) -> None:
        self._data_file = data_file
        self._lock = RLock()
        data_file.parent.mkdir(parents=True, exist_ok=True)
        if not data_file.exists():
            self._write(LocalState())
        # Arquivo inválido causa erro explícito; nunca apagamos dados para recuperar.
        self._read()
        self._recover_scans()

    @property
    def name(self):
        return "json-local"

    @property
    def runs_dir(self):
        return self._data_file.parent / "runs"

    @property
    def scans_dir(self):
        return self._data_file.parent / "scans"

    @property
    def clear_marker(self):
        return self._data_file.with_suffix(".clear-pending.json")

    def clear_reports(self):
        """Limpeza explícita do protótipo, sob o mesmo bloqueio da ingestão."""
        with self._lock:
            state = self._read()
            if any(run.status in {"queued", "running"} for run in state.runs):
                raise ValueError(
                    "Aguarde a análise em andamento terminar antes de limpar os dados."
                )
            counts = {
                "findings": len(state.findings),
                "runs": len(state.runs),
                "scans": len(self._scan_records()),
            }
            state.findings = []
            state.runs = []
            state.processed_scan_ids = []
            for asset in state.assets:
                asset.open_findings = 0
                asset.last_scan_at = None
                asset.scan_metadata = None
                asset.assessment_status = "not_assessed"
                asset.risk_score = None
                asset.compliance = None
            # Se o processo cair, a próxima leitura termina a limpeza antes de
            # recuperar scans. Assim, relatórios excluídos não voltam ao painel.
            self._atomic_json(self.clear_marker, state.model_dump(mode="json", by_alias=True))
            self._finish_clear()
            return counts

    def _finish_clear(self):
        if not self.clear_marker.exists():
            return
        state = LocalState.model_validate_json(self.clear_marker.read_text(encoding="utf-8"))
        root = self._data_file.parent.resolve()
        for directory in (self.scans_dir, self.runs_dir):
            if directory.is_symlink() or directory.resolve().parent != root:
                raise ValueError("Pasta de relatórios fora do armazenamento local.")
            if directory.exists():
                shutil.rmtree(directory)
        self._write(state)
        self.clear_marker.unlink()

    def list_scans(self):
        with self._lock:
            self._finish_clear()
            records = self._scan_records()
        return [
            {
                "received_at": record["received_at"],
                "source": record["payload"]["source"],
                "asset": record["payload"]["asset"],
                "scan": record["payload"]["scan"],
                "findings_count": len(record["payload"]["findings"]),
            }
            for record in reversed(records)
        ]

    def _scan_records(self):
        return sorted(
            [
                json.loads(path.read_text(encoding="utf-8"))
                for path in self.scans_dir.glob("*.json")
            ],
            key=lambda record: (record["received_at"], record["payload"]["scan"]["id"]),
        )

    def _recover_scans(self):
        # Cada varredura é um registro imutável. Se cair entre as duas gravações,
        # a inicialização seguinte termina a atualização do índice, sem duplicar dados.
        state = self._read()
        changed = False
        for record in self._scan_records():
            if record["payload"]["scan"]["id"] not in state.processed_scan_ids:
                self._apply_scan(state, record)
                changed = True
        if changed:
            self._write(state)

    def ingest_scan(self, envelope: ScanEnvelope, content_digest: str):
        with self._lock:
            self._recover_scans()
            scan_id = str(envelope.scan.id)
            path = self.scans_dir / f"{scan_id}.json"
            if path.exists():
                previous = json.loads(path.read_text(encoding="utf-8"))
                if previous["content_digest"] != content_digest:
                    raise ValueError("scan.id já existe com conteúdo diferente.")
                return {
                    "scan_id": scan_id,
                    "received": len(envelope.findings),
                    "replayed": True,
                    "created": 0,
                    "updated": 0,
                    "duplicates": len(envelope.findings),
                }
            record = {
                "received_at": datetime.now(UTC).isoformat(),
                "content_digest": content_digest,
                "payload": envelope.model_dump(mode="json"),
            }
            state = self._read()
            counts = self._apply_scan(state, record)
            self._atomic_json(path, record)
            self._write(state)
            return {
                "scan_id": scan_id,
                "received": len(envelope.findings),
                "replayed": False,
                **counts,
            }

    def _apply_scan(self, state, record):
        envelope = ScanEnvelope.model_validate(record["payload"])
        stamp = datetime.fromisoformat(record["received_at"])
        incoming = normalize(envelope, stamp)
        existing = {f.id: index for index, f in enumerate(state.findings)}
        created = updated = duplicates = 0
        for finding in incoming:
            index = existing.get(finding.id)
            if index is None:
                state.findings.append(finding)
                created += 1
            else:
                previous = state.findings[index]
                previous.occurrences += 1
                if previous.detected_at and finding.detected_at < previous.detected_at:
                    duplicates += 1
                    continue
                finding.occurrences = previous.occurrences
                finding.imported_at = previous.imported_at
                finding.status = previous.status
                # Nova varredura exige análise própria; não reutilizar a conclusão antiga.
                state.findings[index] = finding
                updated += 1
        asset = next((a for a in state.assets if a.id == envelope.asset.id), None)
        if asset is None:
            state.assets.insert(0, imported_asset(envelope, stamp))
        elif asset.last_scan_at is None or envelope.scan.finished_at >= asset.last_scan_at:
            # Mantém a configuração humana; atualiza somente metadados observados no scan.
            asset.last_scan_at = envelope.scan.finished_at
            asset.last_seen_at = stamp
            asset.scan_metadata = envelope.asset.model_dump(mode="json")
            if envelope.scan.status != "failed":
                asset.assessment_status = "assessed"
        state.processed_scan_ids.append(str(envelope.scan.id))
        return {
            "created": created,
            "updated": updated,
            "duplicates": duplicates + len(envelope.findings) - len(incoming),
        }

    def dashboard(self) -> DashboardData:
        with self._lock:
            state = self._read()
        findings = state.findings
        active = [f for f in findings if f.status not in {"resolved", "false_positive"}]
        reviewed = [f for f in findings if f.analysis is not None]
        counts = Counter(f.analysis.classification for f in reviewed)
        days = {}
        for finding in findings:
            # O gráfico mostra recebimentos reais, não uma série de risco inventada.
            observed = finding.imported_at or finding.detected_at
            if observed is None:
                continue
            day = observed.date()
            point = days.setdefault(
                day, dict(critical=0, high=0, medium=0, low=0, info=0, unknown=0)
            )
            point[finding.technical_severity or "unknown"] += 1
        for asset in state.assets:
            linked = [f for f in findings if f.asset_id == asset.id]
            asset.open_findings = sum(
                f.status not in {"resolved", "false_positive"} for f in linked
            )
            asset.risk_score = None
            asset.compliance = None
            if linked:
                asset.assessment_status = "assessed"
        return DashboardData(
            assets=state.assets,
            findings=findings,
            agents=[],
            alerts=[],
            integrations=[],
            metrics=MetricSummary(
                open_findings=len(active),
                critical_findings=sum(f.technical_severity == "critical" for f in active),
                alerts_reviewed=len(reviewed),
                correlation_rate=sum(f.asset_id is not None for f in findings) / len(findings)
                if findings
                else 0,
                monitored_assets=sum(a.registry_status == "active" for a in state.assets),
                true_positives=counts["true_positive"],
                false_positives=counts["false_positive"],
                inconclusive=counts["inconclusive"],
                pending_analysis=len(findings) - len(reviewed),
            ),
            trend=[TrendPoint(date=day, **value) for day, value in sorted(days.items())],
            sources=[
                SourceBreakdown(
                    source=source,
                    findings=sum(f.source == source and f.analysis is None for f in findings),
                    reviewed=sum(f.source == source and f.analysis is not None for f in findings),
                )
                for source in sorted({f.source for f in findings})
            ],
        )

    def list_assets(self):
        return self.dashboard().assets

    def create_asset(self, payload: AssetCreate):
        with self._lock:
            state = self._read()
            self._ensure_unique_identifier(state, payload.identifier)
            asset = Asset(
                id=f"ast-{uuid4().hex[:12]}",
                **payload.model_dump(),
                assessment_status="not_assessed",
                risk_score=None,
                open_findings=0,
                last_scan_at=None,
                last_seen_at=datetime.now(UTC),
                compliance=None,
            )
            state.assets.insert(0, asset)
            self._write(state)
            return asset

    def update_asset(self, asset_id: str, payload: AssetUpdate):
        with self._lock:
            state = self._read()
            for index, asset in enumerate(state.assets):
                if asset.id != asset_id:
                    continue
                changes = payload.model_dump(exclude_unset=True)
                if "identifier" in changes:
                    self._ensure_unique_identifier(state, changes["identifier"], asset_id)
                updated = Asset.model_validate({**asset.model_dump(), **changes})
                state.assets[index] = updated
                self._write(state)
                return updated
        return None

    def list_findings(self):
        return self.dashboard().findings

    def get_finding(self, finding_id):
        return next((f for f in self.list_findings() if f.id == finding_id), None)

    def list_integrations(self):
        return []

    def list_runs(self):
        with self._lock:
            return self._read().runs

    def create_run(self, finding_ids: list[str]):
        with self._lock:
            state = self._read()
            if any(r.status in {"running", "queued"} for r in state.runs):
                raise ValueError("Já existe uma análise em andamento.")
            requested = set(finding_ids)
            chosen = (
                [f for f in state.findings if f.id in requested]
                if requested
                else [f for f in state.findings if f.analysis is None][:50]
            )
            if requested and requested != {f.id for f in chosen}:
                raise ValueError("Um dos findings selecionados não existe.")
            if not chosen:
                raise ValueError("Não há findings pendentes para analisar.")
            run = AnalysisRun(
                id=uuid4().hex,
                status="queued",
                finding_ids=[f.id for f in chosen],
                created_at=datetime.now(UTC),
            )
            state.runs.insert(0, run)
            self._write(state)
            return run, chosen

    def update_run(self, run_id, **changes):
        with self._lock:
            state = self._read()
            for index, run in enumerate(state.runs):
                if run.id == run_id:
                    state.runs[index] = AnalysisRun.model_validate({**run.model_dump(), **changes})
            self._write(state)

    def complete_run(self, run_id: str, analyses: dict[str, FindingAnalysis], originals: dict):
        with self._lock:
            state = self._read()
            run = next(r for r in state.runs if r.id == run_id)
            if set(run.finding_ids) != set(analyses):
                raise ValueError("Resultado incompleto da análise.")
            if any(f.original != originals.get(f.id) for f in state.findings if f.id in analyses):
                raise ValueError("Novas evidências chegaram durante a análise. Execute novamente.")
            for finding in state.findings:
                if finding.id in analyses:
                    finding.analysis = analyses[finding.id]
                    # A sugestão da IA não resolve nem exclui automaticamente o finding.
            run.status = "completed"
            run.finished_at = datetime.now(UTC)
            run.stage = "Concluída"
            self._write(state)

    def recover_interrupted(self):
        with self._lock:
            state = self._read()
            for run in state.runs:
                if run.status in {"queued", "running"}:
                    run.status = "interrupted"
                    run.error = "Backend reiniciado durante a execução. Inicie uma nova análise."
                    run.finished_at = datetime.now(UTC)
            self._write(state)

    def _read(self):
        self._finish_clear()
        state = LocalState.model_validate_json(self._data_file.read_text(encoding="utf-8"))
        # Cadastros antigos pendentes vieram da descoberta. Preservamos essa
        # origem ao salvar sua revisão, sem confundi-la com o status atual.
        for asset in state.assets:
            if asset.registry_status == "pending_review" and asset.registration_source == "manual":
                asset.registration_source = "integration"
        return state

    def _write(self, state):
        self._atomic_json(self._data_file, state.model_dump(mode="json", by_alias=True))

    @staticmethod
    def _atomic_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)

    @staticmethod
    def _ensure_unique_identifier(state, identifier, ignored_id=None):
        if any(
            a.id != ignored_id and a.identifier.strip().casefold() == identifier.strip().casefold()
            for a in state.assets
        ):
            raise DuplicateAssetIdentifierError(identifier)
