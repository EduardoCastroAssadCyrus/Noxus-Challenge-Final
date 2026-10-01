"""Executa o Challenge3 em outro processo, com arquivos próprios para cada análise."""

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from datetime import UTC, datetime
from threading import Event

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import FindingAnalysis


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    classification: str = Field(pattern="^(true_positive|false_positive|inconclusive)$")
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)
    evidence: list[str]


def validate_decisions(output, findings, run_id):
    decisions = [Decision.model_validate(item) for item in output["decisions"]]
    expected = {f.id for f in findings}
    ids = [d.id for d in decisions]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("IDs inválidos na resposta da IA.")
    if output.get("originals") != {f.id: f.original for f in findings}:
        raise ValueError("As evidências originais foram modificadas.")
    return {
        d.id: FindingAnalysis(
            **d.model_dump(exclude={"id"}),
            run_id=run_id,
            analyzed_at=datetime.now(UTC),
        )
        for d in decisions
    }


class LocalCrewRunner:
    def __init__(self, settings, repository):
        self.settings = settings
        self.repository = repository
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="noxus-crew")
        self.stop = Event()
        self._status_cache = None
        self._status_time = 0

    @property
    def bridge(self):
        return self.settings.crew_project / "noxus_bridge.py"

    def process_options(self):
        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "OTEL_SDK_DISABLED": "true",
            "CREWAI_TELEMETRY_DISABLED": "true",
            "CREWAI_TRACING_ENABLED": "false",
        }
        return dict(
            cwd=self.settings.crew_project,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    def availability(self, refresh=False):
        if not refresh and self._status_cache and time.monotonic() - self._status_time < 15:
            return self._status_cache
        status = {"ready": False, "provider": None, "error": None}
        if self.settings.crew_provider != "challenge3" or not self.bridge.is_file():
            status["error"] = "Ponte do Challenge3 não configurada."
        else:
            try:
                result = subprocess.run(
                    [sys.executable, str(self.bridge), "--check"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=20,
                    **self.process_options(),
                )
                status.update(json.loads(result.stdout.strip().splitlines()[-1]))
                if result.returncode:
                    status["ready"] = False
            except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
                status["error"] = (
                    "Instale as dependências CrewAI e confira a configuração do Challenge3."
                )
        self._status_cache, self._status_time = status, time.monotonic()
        return status

    def submit(self, run, findings):
        self.pool.submit(self._execute, run, findings)

    def _execute(self, run, findings):
        directory = self.repository.runs_dir / run.id
        source, output, progress = [
            directory / name for name in ("input.json", "output.json", "progress.json")
        ]
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # Snapshot imutável do lote escolhido; novos imports não alteram esta análise.
            source.write_text(
                json.dumps(
                    {
                        "contract_notes": (
                            "original contém o contexto NOXUS 1.0 e finding normalizado. "
                            "source é o produtor; scan.category é a categoria; "
                            "scan.tool é a ferramenta. developer indica o executor, "
                            "não autoria da falha. Severidade null é desconhecida. "
                            "SECRET tem textos sanitizados; não tente reconstruir credenciais. "
                            "APIs consumidas são declaradas, não descobertas."
                        ),
                        "findings": [{"id": f.id, "original": f.original} for f in findings],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.repository.update_run(run.id, status="running", stage="Iniciando agentes")
            with subprocess.Popen(
                [
                    sys.executable,
                    str(self.bridge),
                    "--input",
                    str(source.resolve()),
                    "--output",
                    str(output.resolve()),
                    "--progress",
                    str(progress.resolve()),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **self.process_options(),
            ) as process:
                deadline = time.monotonic() + self.settings.crew_timeout_seconds
                while process.poll() is None:
                    if self.stop.wait(0.25) or time.monotonic() > deadline:
                        process.kill()
                        process.wait()
                        raise TimeoutError
                if process.returncode != 0:
                    raise RuntimeError
            result = json.loads(output.read_text(encoding="utf-8"))
            analyses = validate_decisions(result, findings, run.id)
            self.repository.complete_run(run.id, analyses, {f.id: f.original for f in findings})
        except Exception:
            self.repository.update_run(
                run.id,
                status="interrupted" if self.stop.is_set() else "failed",
                finished_at=datetime.now(UTC),
                error="Análise não aplicada. Confira credenciais, modelo, conexão e prazo. "
                "Respostas incompletas ou inválidas são rejeitadas. Os originais foram mantidos.",
            )

    def runs(self):
        runs = self.repository.list_runs()
        for run in runs:
            if run.status == "running":
                progress = self.repository.runs_dir / run.id / "progress.json"
                with suppress(OSError, ValueError, KeyError):
                    run.stage = json.loads(progress.read_text(encoding="utf-8"))["stage"]
        return runs

    def close(self):
        self.stop.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
