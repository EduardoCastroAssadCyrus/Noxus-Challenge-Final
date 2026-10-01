import json
from uuid import uuid4

import pytest

from app.ai.local_runner import validate_decisions
from app.repositories.json_repository import JsonNoxusRepository

from .conftest import envelope
from .test_local_flow import import_into, output_for


def test_clear_removes_reviewed_pending_assets_and_files(client, asset_payload):
    repo = client.app.state.repository
    manual = client.post("/api/v1/assets", json=asset_payload).json()
    import_into(repo)
    run, batch = repo.create_run([])
    output = output_for(batch)
    repo.complete_run(run.id, validate_decisions(output, batch, run.id), output["originals"])
    import_into(repo, envelope("sonar", str(uuid4())))
    run_dir = repo.runs_dir / run.id
    run_dir.mkdir(parents=True)
    (run_dir / "output.json").write_text(json.dumps(output), encoding="utf-8")
    connection = repo.runs_dir.parent / "agent-connection.json"
    connection.write_text('{"test": true}', encoding="utf-8")

    response = client.post("/api/v1/reports/clear", json={"confirmation": "LIMPAR DADOS"})
    assert response.status_code == 200
    assert response.json() == {"assets": 2, "findings": 2, "scans": 2, "runs": 1}
    reopened = JsonNoxusRepository(repo._data_file)
    assert reopened.list_findings() == reopened.list_scans() == reopened.list_runs() == []
    assert reopened.list_assets() == []
    assert connection.read_text(encoding="utf-8") == '{"test": true}'
    assert not repo.runs_dir.exists() and not repo.scans_dir.exists()
    # O mesmo relatório pode ser importado de novo para outro teste.
    assert import_into(reopened)["created"] == 1


def test_clear_requires_confirmation_and_blocks_active_analysis(client):
    repo = client.app.state.repository
    import_into(repo)
    assert client.post("/api/v1/reports/clear", json={}).status_code == 422
    repo.create_run([])
    response = client.post("/api/v1/reports/clear", json={"confirmation": "LIMPAR DADOS"})
    assert response.status_code == 409
    assert len(repo.list_findings()) == len(repo.list_scans()) == 1


def test_clear_disabled_in_production(client):
    client.app.state.settings.environment = "production"
    assert (
        client.post("/api/v1/reports/clear", json={"confirmation": "LIMPAR DADOS"}).status_code
        == 403
    )


def test_interrupted_clear_finishes_before_scan_recovery(tmp_path, monkeypatch):
    repo = JsonNoxusRepository(tmp_path / "state.json")
    import_into(repo)
    with monkeypatch.context() as patch:
        patch.setattr(repo, "_write", lambda state: (_ for _ in ()).throw(OSError("queda")))
        with pytest.raises(OSError):
            repo.clear_reports()
    assert repo.clear_marker.exists()
    reopened = JsonNoxusRepository(repo._data_file)
    assert reopened.list_findings() == reopened.list_scans() == []
    assert not reopened.clear_marker.exists()


def test_review_preserves_automatic_origin(client):
    import_into(client.app.state.repository)
    response = client.patch("/api/v1/assets/backend-test", json={"registryStatus": "active"})
    assert response.status_code == 200
    assert response.json()["registrationSource"] == "integration"
    assert response.json()["registryStatus"] == "active"
    assert (
        client.patch(
            "/api/v1/assets/backend-test", json={"registrationSource": "manual"}
        ).status_code
        == 422
    )


def test_delete_asset_unlinks_findings_and_returns_404(client):
    repo = client.app.state.repository
    import_into(repo)
    assert client.delete("/api/v1/assets/backend-test").status_code == 204
    assert repo.list_assets() == []
    assert repo.list_findings()[0].asset_id is None
    assert client.delete("/api/v1/assets/backend-test").status_code == 404
