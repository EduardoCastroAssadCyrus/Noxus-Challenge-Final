def test_health_exposes_disabled_integrations(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "noxus-aspm-api",
        "environment": "test",
        "dataStore": "json-local",
        "chatProvider": "disabled",
        "crewProvider": "challenge3",
    }


def test_dashboard_uses_frontend_camel_case_contract(client):
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["monitoredAssets"] == 0
    assert body["assets"] == []
    assert body["findings"] == []
    assert body["metrics"]["complianceScore"] is None


def test_asset_can_be_created_and_updated(client, asset_payload):
    create_response = client.post("/api/v1/assets", json=asset_payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"].startswith("ast-")
    assert created["assessmentStatus"] == "not_assessed"
    assert created["lastScanAt"] is None
    assert created["riskScore"] is None

    update_response = client.patch(
        f"/api/v1/assets/{created['id']}",
        json={"owner": "Squad Plataforma de Clientes", "registryStatus": "pending_review"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["owner"] == "Squad Plataforma de Clientes"
    assert update_response.json()["registryStatus"] == "pending_review"

    dashboard = client.get("/api/v1/dashboard").json()
    persisted = next(asset for asset in dashboard["assets"] if asset["id"] == created["id"])
    assert persisted["owner"] == "Squad Plataforma de Clientes"


def test_duplicate_identifier_is_rejected(client, asset_payload):
    assert client.post("/api/v1/assets", json=asset_payload).status_code == 201

    response = client.post("/api/v1/assets", json=asset_payload)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "duplicate_asset_identifier"


def test_missing_resources_return_404(client):
    assert client.get("/api/v1/findings/unknown").status_code == 404
    assert client.patch("/api/v1/assets/unknown", json={"owner": "Outro time"}).status_code == 404


def test_chat_and_discovery_are_explicitly_disabled(client):
    chat_response = client.post("/api/v1/chat/messages", json={"content": "Explique NX-4821"})
    discovery_response = client.post("/api/v1/asset-discovery/runs")

    assert chat_response.status_code == 503
    assert chat_response.json()["detail"]["code"] == "chat_provider_not_configured"
    assert discovery_response.status_code == 503
    assert discovery_response.json()["detail"]["code"] == "asset_discovery_not_configured"
