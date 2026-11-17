
import httpx
import pytest

from app.platforms.mastodon import MastodonPlatform


class TestableMastodonPlatform(MastodonPlatform):
    async def publish(self, message):
        return {}


@pytest.mark.asyncio
async def test_mastodon_verification_failure_returns_false(monkeypatch):
    platform = TestableMastodonPlatform()

    async def mock_get(self, url, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await platform.verify_public_access("12345")

    assert result is False

from unittest.mock import AsyncMock

from app.platforms import mastodon


@pytest.mark.asyncio
async def test_mastodon_publish_succeeds_when_verification_fails(monkeypatch):
    platform = MastodonPlatform()

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "id": "12345",
                "url": "https://mastodon.social/@example/12345"
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(mastodon.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(mastodon.settings, "mastodon_instance_url", "https://mastodon.social")
    monkeypatch.setattr(mastodon.settings, "mastodon_access_token", "fake-token")

    monkeypatch.setattr(
        platform,
        "verify_public_access",
        AsyncMock(return_value=False)
    )

    result = await platform.publish("Check out our platform https://example.com")

    assert result["status"] == "success"
    assert result["public_access"] is False
    assert result["posted_url"] == "https://mastodon.social/@example/12345"
