import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

ALLOWED_ORIGIN = "http://localhost:5173"


@pytest.fixture
def client():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@db.test:5432/test",
        jwt_secret="khoa-test-chi-dung-trong-pytest-du-32-ky-tu",
        cors_origins=[ALLOWED_ORIGIN],
    )
    transport = ASGITransport(app=create_app(settings))
    return AsyncClient(transport=transport, base_url="http://test")


async def test_preflight_from_allowed_origin(client):
    async with client:
        response = await client.options(
            "/health",
            headers={"Origin": ALLOWED_ORIGIN, "Access-Control-Request-Method": "POST"},
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


async def test_simple_request_from_allowed_origin(client):
    async with client:
        response = await client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


async def test_disallowed_origin_gets_no_cors_header(client):
    async with client:
        preflight = await client.options(
            "/health",
            headers={"Origin": "http://evil.test", "Access-Control-Request-Method": "GET"},
        )
        response = await client.get("/health", headers={"Origin": "http://evil.test"})

    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in response.headers
