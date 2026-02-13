from __future__ import annotations

from fastapi.testclient import TestClient

from appealpilot.api.app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_classify_endpoint() -> None:
    response = client.post(
        "/classify",
        json={
            "denial_text": "Payer: Blue Cross. Denial Reason: not medically necessary. CPT 72148."
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "classification" in body
    assert body["classification"]["category"] in {"medical_necessity", "other"}
