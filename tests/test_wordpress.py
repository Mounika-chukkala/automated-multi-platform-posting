
import httpx
import pytest

from app.platforms.wordpress import WordPressPlatform



@pytest.mark.asyncio
async def test_verification_failure_returns_false(monkeypatch):
    platform = WordPressPlatform()

    async def mock_get(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request)

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get,
    )

    result = await platform.verify_public_access("12345")

    assert result is False

@pytest.mark.asyncio
async def test_successful_publish_with_failed_verification(monkeypatch):
    platform = WordPressPlatform()

    async def mock_post(self, url, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "ID": 12345,
                "URL": "https://example.wordpress.com/12345",
            },
            request=request,
        )

    async def mock_get(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request)

    monkeypatch.setattr(
        httpx.AsyncClient, "post", mock_post
    )
    monkeypatch.setattr(
        httpx.AsyncClient, "get", mock_get
    )

    monkeypatch.setattr(
        "app.platforms.wordpress.settings.wordpress_access_token",
        "fake-token",
    )
    monkeypatch.setattr(
        "app.platforms.wordpress.settings.wordpress_site_url",
        "https://example.wordpress.com",
    )

    result = await platform.publish(
        "Check out our platform https://example.com"
    )

    assert result["status"] == "success"
    assert result["public_access"] is False
    assert result["posted_url"] == (
        "https://example.wordpress.com/12345"
    )
