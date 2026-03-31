from fastapi.testclient import TestClient

from orchestrator.api.main import build_app


def test_root_endpoint():
    app = build_app()
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["docs"] == "/docs"


def test_health_endpoint():
    app = build_app()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_ui_endpoint():
    app = build_app()
    with TestClient(app) as client:
        response = client.get("/demo")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Run Sample Job" in response.text
