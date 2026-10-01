import copy
from uuid import uuid4

import pytest
from pydantic import SecretStr

from .conftest import envelope


@pytest.mark.parametrize(
    "tool",
    [
        "semgrep",
        "gitleaks",
        "dependency-check",
        "nikto",
        "sonar",
        "dependency-reputation",
        "extension-reputation",
    ],
)
def test_all_producers_tools_and_categories(client, tool):
    payload = envelope(tool)
    if tool in {"dependency-check", "dependency-reputation", "extension-reputation"}:
        payload["findings"][0]["location"] = {}
        payload["findings"][0]["dependency"] = {
            "name": "publisher.extension" if tool == "extension-reputation" else "package-x",
            "version": "1.2.3",
            "ecosystem": "vscode" if tool == "extension-reputation" else "npm",
        }
    elif tool == "nikto":
        payload["findings"][0]["location"] = {"url": "http://localhost:8080/admin"}
    response = client.post("/api/v1/imports", json=payload)
    assert response.status_code == 201, response.text
    finding = client.get("/api/v1/findings").json()[0]
    assert finding["source"] == payload["scan"]["category"]
    assert finding["producer"] == payload["source"]
    assert finding["tool"] == tool
    assert finding["original"]["finding"]["cve"] == ["CVE-2026-1234"]
    assert finding["original"]["finding"]["cwe"] == ["CWE-89"]


@pytest.mark.parametrize("status", ["completed", "partial", "failed"])
def test_empty_and_failed_scans_are_saved_without_inventing_findings(client, status):
    payload = envelope()
    payload["findings"] = []
    payload["scan"]["status"] = status
    payload["scan"]["error"] = "Ferramenta indisponível" if status == "failed" else None
    result = client.post("/api/v1/imports", json=payload)
    assert result.status_code == 201
    assert result.json()["received"] == result.json()["created"] == 0
    history = client.get("/api/v1/scans").json()
    assert history[0]["scan"]["status"] == status and history[0]["findings_count"] == 0
    assert client.get("/api/v1/findings").json() == []
    assert len(client.get("/api/v1/assets").json()) == 1


def test_unknown_severity_is_not_estimated(client):
    payload = envelope()
    payload["findings"][0]["severity"] = None
    client.post("/api/v1/imports", json=payload)
    data = client.get("/api/v1/dashboard").json()
    assert data["findings"][0]["technicalSeverity"] is None
    assert data["findings"][0]["operationalPriority"] is None
    assert data["metrics"]["criticalFindings"] == 0
    assert data["trend"][0]["unknown"] == 1
    rows = client.get("/api/v1/findings").json()
    assert rows[0]["technicalSeverity"] is None
    assert client.get(f"/api/v1/findings/{rows[0]['id']}").json()["technicalSeverity"] is None


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), "2.0"),
        (("source",), "SAST"),
        (("scan", "id"), "not-a-uuid"),
        (("scan", "category"), "DAST"),
        (("scan", "started_at"), "2026-10-01T10:00:00"),
        (("scan", "finished_at"), "2026-09-01T10:00:00Z"),
        (("scan", "status"), "failed"),
        (("scan", "trigger"), "unknown-trigger"),
        (("asset", "repository_url"), "https://user:password@example.com/repo"),
        (("asset", "application_url"), "https://example.com/?token=secret"),
        (("asset", "repository_url"), "https://example.com/repo#fragment"),
        (("asset", "commit"), "not-hex"),
        (("asset", "consumed_apis", 0, "base_url"), "ftp://example.com"),
        (("findings", 0, "severity"), "HIGH"),
        (("findings", 0, "cwe"), ["89"]),
        (("findings", 0, "cve"), ["invalid"]),
        (("findings", 0, "location", "line"), 0),
        (("findings", 0, "location", "column"), True),
        (("findings", 0, "location", "line"), "42"),
        (("findings", 0, "location"), {}),
        (("findings", 0, "location"), {"url": "http://localhost", "line": 1}),
        (("findings", 0, "Secret"), "DO-NOT-ECHO"),
        (("findings", 0, "Match"), "DO-NOT-ECHO"),
        (("findings", 0, "snippet"), "DO-NOT-ECHO"),
    ],
)
def test_invalid_contract_rejected_atomically_without_echo(client, path, value):
    payload = envelope()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    result = client.post("/api/v1/imports", json=payload)
    assert result.status_code == 422, result.text
    assert "DO-NOT-ECHO" not in result.text
    assert '"input"' not in result.text
    assert client.get("/api/v1/scans").json() == []
    assert client.get("/api/v1/assets").json() == []


def test_failed_scan_cannot_contain_findings(client):
    payload = envelope()
    payload["scan"].update(status="failed", error="Falhou")
    assert client.post("/api/v1/imports", json=payload).status_code == 422


def test_wrong_producer_tool_and_old_flat_format_are_rejected(client):
    payload = envelope("sonar")
    payload["source"] = "noxus-agent"
    assert client.post("/api/v1/imports", json=payload).status_code == 422
    assert (
        client.post(
            "/api/v1/imports",
            json={"findings": [{"id": "x", "tool": "SAST", "title": "x", "severity": "HIGH"}]},
        ).status_code
        == 422
    )


def test_secret_is_sanitized_in_every_saved_json_and_replay_hash_detects_changes(client):
    payload = envelope("gitleaks")
    for field in ("title", "description", "recommendation"):
        payload["findings"][0][field] = "SENSITIVE-TEST-MARKER"
    assert client.post("/api/v1/imports", json=payload).status_code == 201
    assert client.post("/api/v1/imports", json=payload).json()["replayed"] is True
    payload["findings"][0]["title"] = "DIFFERENT-SENSITIVE-VALUE"
    assert client.post("/api/v1/imports", json=payload).status_code == 409
    root = client.app.state.repository.scans_dir.parent
    for path in root.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "SENSITIVE-TEST-MARKER" not in text and "DIFFERENT-SENSITIVE-VALUE" not in text
    assert "SENSITIVE-TEST-MARKER" not in client.get("/api/v1/dashboard").text


def test_duplicates_new_scan_and_late_scan_do_not_multiply_rows_or_revert(client):
    payload = envelope()
    payload["findings"] *= 2
    first = client.post("/api/v1/imports", json=payload).json()
    assert first["created"] == 1 and first["duplicates"] == 1
    later = copy.deepcopy(payload)
    later["scan"].update(
        id=str(uuid4()), started_at="2026-10-02T10:00:00Z", finished_at="2026-10-02T10:00:05Z"
    )
    later["findings"][0]["severity"] = "critical"
    assert client.post("/api/v1/imports", json=later).json()["updated"] == 1
    payload["scan"]["id"] = str(uuid4())
    client.post("/api/v1/imports", json=payload)
    rows = client.get("/api/v1/findings").json()
    assert len(rows) == 1 and rows[0]["technicalSeverity"] == "critical"
    assert rows[0]["occurrences"] == 3
    empty = envelope(scan_id=str(uuid4()))
    empty["findings"] = []
    client.post("/api/v1/imports", json=empty)
    assert client.get("/api/v1/findings").json()[0]["status"] == "open"


def test_routes_api_key_extension_and_schema(client):
    payload = envelope()
    client.app.state.settings.ingestion_api_key = None
    assert client.post("/api/findings", json=payload).status_code == 503
    client.app.state.settings.ingestion_api_key = SecretStr("test-key")
    assert client.post("/api/findings", json=payload).status_code == 401
    headers = {"X-API-Key": "test-key"}
    assert client.post("/api/findings", json=payload, headers=headers).status_code == 200
    assert (
        client.post(
            "/api/integrations/noxus-vscode/scans", json=payload, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/integrations/noxus-vscode/scans",
            json=envelope("sonar", str(uuid4())),
            headers=headers,
        ).status_code
        == 200
    )
    assert client.get("/api/schema", headers=headers).json()["properties"]["findings"]


@pytest.mark.parametrize("chunked", [False, True])
def test_body_limit_is_10_mib_even_without_content_length(client, chunked):
    body = b" " * (10 * 1024 * 1024 + 1)
    content = iter([body[:1024], body[1024:]]) if chunked else body
    result = client.post(
        "/api/v1/imports", content=content, headers={"Content-Type": "application/json"}
    )
    assert result.status_code == 413
    assert client.get("/api/v1/scans").json() == []


def test_bad_json_does_not_echo_body(client):
    result = client.post(
        "/api/v1/imports",
        content='{"secret": "DO-NOT-ECHO",',
        headers={"Content-Type": "application/json"},
    )
    assert result.status_code == 422 and "DO-NOT-ECHO" not in result.text
