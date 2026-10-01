from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def envelope(tool="semgrep", scan_id="a578af66-a49a-4913-909f-3dd1af647813"):
    """Envelope sintético restrito aos testes, nunca carregado pelo dashboard."""
    categories = {
        "semgrep": "SAST",
        "sonar": "SAST",
        "gitleaks": "SECRET",
        "nikto": "DAST",
        "dependency-check": "SCA",
        "dependency-reputation": "SCA",
        "extension-reputation": "EXTENSION",
    }
    extension = tool in {"sonar", "dependency-reputation", "extension-reputation"}
    return {
        "schema_version": "1.0",
        "source": "noxus-vscode-extension" if extension else "noxus-agent",
        "developer": {"name": "Executor de teste", "role": "Dev", "team": "Back-End"},
        "asset": {
            "id": "backend-test",
            "name": "Backend de teste",
            "type": "web-api",
            "repository_url": "https://github.com/exemplo/backend",
            "branch": "main",
            "commit": None,
            "local_ip": "127.0.0.1",
            "application_url": "http://localhost:8080",
            "consumed_apis": [
                {"name": "Pedidos", "base_url": "http://localhost:8081", "source": "manual"}
            ],
        },
        "scan": {
            "id": scan_id,
            "tool": tool,
            "tool_version": None,
            "category": categories[tool],
            "started_at": "2026-10-01T10:00:00-03:00",
            "finished_at": "2026-10-01T10:00:05-03:00",
            "status": "completed",
            "trigger": "ide-save" if extension else "manual",
            "error": None,
        },
        "findings": [
            {
                "title": "Achado sintético",
                "description": "Somente para teste",
                "rule_id": "test.sql-injection",
                "severity": "high",
                "cwe": ["CWE-89"],
                "cve": ["CVE-2026-1234"],
                "location": {"file": "src/db.py", "line": 42, "column": 8},
                "dependency": None,
                "recommendation": "Use consultas parametrizadas.",
            }
        ],
    }


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    settings = Settings(
        environment="test",
        data_file=tmp_path / "noxus.test.json",
        cors_origins="http://localhost:3000",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def asset_payload() -> dict:
    return {
        "name": "API de Clientes",
        "applicationName": "Customer 360",
        "type": "api",
        "identifier": "https://customers.noxus.example",
        "repo": "pride/customers-api",
        "environment": "production",
        "owner": "Squad Clientes",
        "businessCriticality": "high",
        "access": "public_internet",
        "location": {
            "hosting": "public_cloud",
            "provider": "AWS",
            "region": "sa-east-1",
        },
        "dataClassification": "restricted",
        "containsRealData": True,
        "technologies": ["Python", "FastAPI"],
        "registrationSource": "manual",
        "registryStatus": "active",
        "discoveryConfidence": None,
    }
