import asyncio

from httpx import ASGITransport, AsyncClient, Response

from agent.main import app


async def request_health() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


def test_health_endpoint_is_healthy() -> None:
    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "jarvis-agent",
        "version": "0.2.0",
    }


def test_health_response_matches_openapi_schema() -> None:
    schema = app.openapi()["components"]["schemas"]["HealthResponse"]

    assert set(schema["required"]) == {"status", "service", "version"}
    assert schema["properties"]["status"]["const"] == "ok"
    assert schema["properties"]["service"]["const"] == "jarvis-agent"
