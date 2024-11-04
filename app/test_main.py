import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_webhook_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook",
            json={
                "message": "Hello, world!",
                "callback_url": "http://web:8000/callback"
            }
        )
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["status"] == "Processing"

@pytest.mark.asyncio
async def test_webhook_invalid_url():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook",
            json={
                "message": "Test message",
                "callback_url": "invalid-url"
            }
        )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Input should be a valid URL, relative URL without a base"

@pytest.mark.asyncio
async def test_webhook_missing_field():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook",
            json={
                "message": "Test message"
                # callback_url отсутствует
            }
        )
    assert response.status_code == 422
    assert "detail" in response.json()


            

@pytest.mark.asyncio
async def test_rate_limiting():
    async with AsyncClient(app=app, base_url="http://test") as client:
        for _ in range(5):
            await client.post(
                "/webhook",
                json={
                    "message": "Rate limit test",
                    "callback_url": "http://web:8000/callback"
                }
            )
        response = await client.post(
            "/webhook",
            json={
                "message": "Rate limit test",
                "callback_url": "http://web:8000/callback"
            }
        )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

