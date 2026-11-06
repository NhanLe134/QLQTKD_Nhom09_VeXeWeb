import httpx
import pytest

LOOKUP_URL = "/api/v1/bookings/lookup"
EXCHANGE_URL = "/api/v1/bookings/exchange"


async def test_lookup_tickets_by_invalid_phone(client):
    response = await client.get(f"{LOOKUP_URL}?phone=123")
    assert response.status_code == 422


async def test_lookup_tickets_by_nonexistent_phone(client, seeded):
    response = await client.get(f"{LOOKUP_URL}?phone=0999999999")
    assert response.status_code == 200
    assert response.json() == []


async def test_exchange_ticket_n8n_connection_error(client, seeded):
    # n8n is not running on localhost:5678 in pytest environment -> returns 502 with helpful message
    response = await client.post(
        EXCHANGE_URL,
        json={
            "ve_id": "VE100001",
            "chuyen_xe_moi_id": "CX100001",
            "ghe_moi_id": "GH100001",
        },
    )
    assert response.status_code == 502
    assert "n8n Webhook" in response.json()["detail"]


async def test_exchange_ticket_n8n_mock_success(client, monkeypatch):
    class MockResponse:
        status_code = 200

        def json(self):
            return {
                "status": "success",
                "message": "Đổi vé thành công",
                "ve_id": "VE100001",
                "chuyen_xe_moi_id": "CX100002",
                "so_ghe_moi": "B01",
            }

    async def mock_post(self, url, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    response = await client.post(
        EXCHANGE_URL,
        json={
            "ve_id": "VE100001",
            "chuyen_xe_moi_id": "CX100002",
            "ghe_moi_id": "GH100005",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["so_ghe_moi"] == "B01"
