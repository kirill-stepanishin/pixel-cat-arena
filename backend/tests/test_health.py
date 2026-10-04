from fastapi.testclient import TestClient

from app.main import app


def test_health_requires_database_configuration(monkeypatch):
    from app import db

    monkeypatch.setattr(db, "session_factory", None)
    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "DATABASE_URL is not configured"
