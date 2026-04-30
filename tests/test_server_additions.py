import pytest
from httpx import AsyncClient, ASGITransport
from brain.server import app


@pytest.mark.asyncio
async def test_cors_header_present():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.options(
            "/query",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert "access-control-allow-origin" in res.headers


@pytest.mark.asyncio
async def test_doc_json_variant(tmp_path, monkeypatch):
    import brain.server as srv

    doc = tmp_path / "hello.md"
    doc.write_text("# Hello\n\nworld")
    monkeypatch.setattr(srv, "DOCS_DIR", str(tmp_path))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.get(
            "/doc/hello", headers={"Accept": "application/json"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "hello"
    assert "<h1>" in data["content_html"]


@pytest.mark.asyncio
async def test_spa_fallback_serves_503_when_no_dist():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.get("/some-react-route")
    # 503 when frontend/dist/index.html not built; never 404
    assert res.status_code == 503
