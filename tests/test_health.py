from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_does_not_expose_environment() -> None:
    response = client.get("/health")

    assert "environment" not in response.json()


def test_security_headers_present() -> None:
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"

    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    # The bundled UI loads Google Fonts; the policy must not break it.
    assert "https://fonts.googleapis.com" in csp
    assert "https://fonts.gstatic.com" in csp
