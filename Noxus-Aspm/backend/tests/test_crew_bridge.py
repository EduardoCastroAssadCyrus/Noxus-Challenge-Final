"""Testa agentes e tarefas CrewAI reais com um LLM controlado, sem rede."""

import importlib.util
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.scan_contract import ScanEnvelope
from app.ingestion import normalize

from .conftest import envelope

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"


def test_real_crewai_tasks_without_database(tmp_path, monkeypatch):
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(tmp_path / "storage"))
    crewai = pytest.importorskip("crewai")
    from crewai import BaseLLM

    bridge_path = Path(__file__).parents[1] / "crew_bridge/noxus_bridge.py"
    spec = importlib.util.spec_from_file_location("noxus_bridge_test", bridge_path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    calls = []

    class ControlledLLM(BaseLLM):
        def __init__(self):
            super().__init__(model="controlled-test", temperature=0)

        def call(self, messages, **kwargs):
            calls.append(messages)
            return json.dumps(
                {
                    "decisions": [
                        {
                            "id": "test-only",
                            "classification": "inconclusive",
                            "confidence": 0.5,
                            "reason": "Evidência insuficiente no teste",
                            "evidence": [],
                        }
                    ]
                }
            )

        def supports_function_calling(self):
            return False

    monkeypatch.setattr(crewai, "LLM", lambda **kwargs: ControlledLLM())
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(tmp_path / "storage"))
    configs = {
        key: {"role": key, "backstory": "Agente de teste.", "llm": "test"}
        for key in (
            "vulnerability_analyzer",
            "fp_tp_validator",
            "security_classifier",
            "json_validator",
        )
    }
    monkeypatch.setattr(bridge, "configuration", lambda project: (configs, "ollama", "test"))
    source, output, progress = [
        tmp_path / name for name in ("input.json", "output.json", "progress.json")
    ]
    finding = normalize(ScanEnvelope.model_validate(envelope("sonar")), datetime.now(UTC))[0]
    source.write_text(
        json.dumps({"findings": [{"id": "test-only", "original": finding.original}]}),
        encoding="utf-8",
    )
    bridge.analyze(tmp_path, source, output, progress)
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["decisions"][0]["classification"] == "inconclusive"
    assert result["originals"]["test-only"] == finding.original
    assert all("noxus-vscode-extension" in json.dumps(messages) for messages in calls)
    assert len(calls) >= 4
    assert not list(tmp_path.rglob("*.db"))
    assert not list(tmp_path.rglob("*.sqlite*"))
