from fastapi.testclient import TestClient

from orchestrator.api.main import build_app


def test_health_endpoint():
    app = build_app()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
