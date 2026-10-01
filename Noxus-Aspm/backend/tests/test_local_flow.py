import copy
import json
import time
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.ai.local_runner import validate_decisions
from app.domain.scan_contract import ScanEnvelope
from app.ingestion import digest, normalize
from app.repositories.json_repository import JsonNoxusRepository

from .conftest import envelope


def import_into(repo, payload=None):
    payload = payload or envelope()
    return repo.ingest_scan(ScanEnvelope.model_validate(payload), digest(payload))


def output_for(findings, classification="false_positive"):
    return {
        "decisions": [
            {
                "id": f.id,
                "classification": classification,
                "confidence": 0.7,
                "reason": "Motivo de teste",
                "evidence": ["Evidência"],
            }
            for f in findings
        ],
        "originals": copy.deepcopy({f.id: f.original for f in findings}),
    }


def test_import_idempotent_and_atomic(client):
    payload = envelope()
    result = client.post("/api/v1/imports", json=payload)
    assert result.status_code == 201
    assert result.json()["created"] == 1
    replay = client.post("/api/v1/imports", json=payload).json()
    assert replay["replayed"] is True and replay["created"] == 0
    conflicting = copy.deepcopy(payload)
    conflicting["findings"][0]["title"] = "Alterado"
    assert client.post("/api/v1/imports", json=conflicting).status_code == 409
    findings = client.get("/api/v1/findings").json()
    assert len(findings) == 1
    assert findings[0]["original"]["finding"]["title"] == payload["findings"][0]["title"]
    assert findings[0]["analysis"] is None and findings[0]["riskScore"] is None
    assert len(list(client.app.state.repository.scans_dir.glob("*.json"))) == 1


def test_bad_batch_leaves_store_empty(client):
    payload = envelope()
    bad = copy.deepcopy(payload["findings"][0])
    bad["location"]["line"] = 0
    payload["findings"].append(bad)
    assert client.post("/api/v1/imports", json=payload).status_code == 422
    assert client.get("/api/v1/findings").json() == []
    assert client.get("/api/v1/scans").json() == []


def test_association_uses_envelope_stable_id_without_invented_context(client):
    payload = envelope()
    client.post("/api/v1/imports", json=payload)
    finding = client.get("/api/v1/findings").json()[0]
    asset = client.get("/api/v1/assets").json()[0]
    assert finding["assetId"] == asset["id"] == payload["asset"]["id"]
    assert asset["openFindings"] == 1
    assert asset["owner"] != payload["developer"]["name"]
    assert asset["access"] == asset["environment"] == "unknown"
    assert asset["containsRealData"] is None and asset["businessCriticality"] is None
    assert asset["scanMetadata"] == payload["asset"]
    assert (
        client.patch(
            f"/api/v1/assets/{asset['id']}", json={"owner": "Squad confirmada"}
        ).status_code
        == 200
    )
    sonar = envelope("sonar", str(uuid4()))
    client.post("/api/v1/imports", json=sonar)
    assets = client.get("/api/v1/assets").json()
    assert len(assets) == 1 and assets[0]["owner"] == "Squad confirmada"
    assert len(client.get("/api/v1/findings").json()) == 2  # não correlacionar ferramentas


def test_analysis_preserves_original_and_persists(tmp_path):
    path = tmp_path / "state.json"
    repo = JsonNoxusRepository(path)
    import_into(repo)
    run, batch = repo.create_run([])
    result = output_for(batch)
    repo.complete_run(run.id, validate_decisions(result, batch, run.id), result["originals"])
    reopened = JsonNoxusRepository(path)
    finding = reopened.dashboard().findings[0]
    assert finding.original == batch[0].original
    assert finding.status == "open"
    assert finding.analysis.classification == "false_positive"
    assert reopened.dashboard().metrics.false_positives == 1
    assert reopened.list_runs()[0].status == "completed"


@pytest.mark.parametrize("failure", ["missing", "duplicate", "invented", "original", "confidence"])
def test_invalid_ai_output_is_rejected(failure):
    batch = normalize(ScanEnvelope.model_validate(envelope()), datetime.now(UTC))
    result = output_for(batch)
    if failure == "missing":
        result["decisions"] = []
    if failure == "duplicate":
        result["decisions"] *= 2
    if failure == "invented":
        result["decisions"][0]["id"] = "other"
    if failure == "original":
        result["originals"][batch[0].id]["finding"]["title"] = "Alterado"
    if failure == "confidence":
        result["decisions"][0]["confidence"] = 3
    with pytest.raises(ValueError):
        validate_decisions(result, batch, "run")


def test_busy_and_restart_recovery(tmp_path):
    repo = JsonNoxusRepository(tmp_path / "state.json")
    import_into(repo)
    repo.create_run([])
    with pytest.raises(ValueError):
        repo.create_run([])
    repo.recover_interrupted()
    assert repo.list_runs()[0].status == "interrupted"
    repo.create_run([])


def test_updated_scan_during_analysis_rejects_stale_decisions(tmp_path):
    repo = JsonNoxusRepository(tmp_path / "state.json")
    import_into(repo)
    run, batch = repo.create_run([])
    import_into(repo, envelope(scan_id=str(uuid4())))
    result = output_for(batch)
    with pytest.raises(ValueError, match="Novas evidências"):
        repo.complete_run(run.id, validate_decisions(result, batch, run.id), result["originals"])
    assert repo.list_findings()[0].analysis is None


def test_recover_scan_journal_after_interrupted_index_write(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    repo = JsonNoxusRepository(path)
    monkeypatch.setattr(
        repo, "_write", lambda state: (_ for _ in ()).throw(OSError("Falha de teste"))
    )
    with pytest.raises(OSError):
        import_into(repo)
    reopened = JsonNoxusRepository(path)
    assert len(reopened.list_findings()) == 1
    assert import_into(reopened)["replayed"] is True
    assert reopened.list_findings()[0].occurrences == 1


def test_unconfigured_crew_does_not_fake_success(client, monkeypatch):
    monkeypatch.setattr(
        client.app.state.crew_runner,
        "availability",
        lambda **kwargs: {"ready": False, "error": "Configure a IA"},
    )
    assert client.post("/api/v1/analysis/runs", json={}).status_code == 503
    assert client.get("/api/v1/analysis/runs").json() == []


@pytest.mark.parametrize("tool", ["semgrep", "gitleaks"])
def test_end_to_end_subprocess_protocol(client, tmp_path, monkeypatch, tool):
    bridge = tmp_path / "noxus_bridge.py"
    bridge.write_text(
        "import argparse,json\nfrom pathlib import Path\n"
        "p=argparse.ArgumentParser()\n"
        "for n in ('input','output','progress'): p.add_argument('--'+n)\n"
        "a=p.parse_args()\n"
        "items=json.loads(Path(a.input).read_text(encoding='utf-8'))['findings']\n"
        "r={'decisions':[{'id':f['id'],'classification':'inconclusive','confidence':0.4,"
        "'reason':'Teste do protocolo','evidence':[]} for f in items],"
        "'originals':{f['id']:f['original'] for f in items}}\n"
        "Path(a.output).write_text(json.dumps(r),encoding='utf-8')\n",
        encoding="utf-8",
    )
    runner = client.app.state.crew_runner
    runner.settings.crew_project = tmp_path
    monkeypatch.setattr(runner, "availability", lambda **kwargs: {"ready": True})
    payload = envelope(tool)
    payload["findings"][0]["title"] = "SENSITIVE-TEST-MARKER"
    assert client.post("/api/v1/imports", json=payload).status_code == 201
    response = client.post("/api/v1/analysis/runs", json={})
    assert response.status_code == 202
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        run = client.get("/api/v1/analysis/runs").json()[0]
        if run["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)
    assert run["status"] == "completed"
    finding = client.get("/api/v1/findings").json()[0]
    assert finding["analysis"]["classification"] == "inconclusive"
    snapshot = json.loads(
        (client.app.state.repository.runs_dir / run["id"] / "input.json").read_text(
            encoding="utf-8"
        )
    )
    original = snapshot["findings"][0]["original"]
    assert original["scan"]["tool"] == tool
    assert original["developer"] == payload["developer"]
    assert original["asset"]["consumed_apis"] == payload["asset"]["consumed_apis"]
    if tool == "gitleaks":
        for path in tmp_path.rglob("*.json"):
            assert "SENSITIVE-TEST-MARKER" not in path.read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("*.db")) and not list(tmp_path.rglob("*.sqlite*"))
