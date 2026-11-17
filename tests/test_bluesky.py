
import pytest
import httpx
from app.platforms.bluesky import BlueskyPlatform


@pytest.mark.asyncio
async def test_bluesky_verification_failure_returns_false(monkeypatch):
    platform = BlueskyPlatform()

    class MockResponse:
        def raise_for_status(self):
            request = httpx.Request(
            "GET",
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread"
        )

            response = httpx.Response(
            503,
            request=request
        )

            raise httpx.HTTPStatusError(
            "Simulated API failure",
            request=request,
            response=response
        )
    class MockAsyncClient:
        def __init__(self, timeout=None):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr(
        "app.platforms.bluesky.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = await platform.verify_public_access(
        "at://did:example:123/app.bsky.feed.post/abc"
    )

    assert result is False


from unittest.mock import AsyncMock

from app.platforms import bluesky


@pytest.mark.asyncio
async def test_bluesky_publish_succeeds_when_verification_fails(monkeypatch):
    platform = BlueskyPlatform()

    class FakePost:
        uri = "at://did:example:123/app.bsky.feed.post/abc"

    class FakeClient:
        async def login(self, handle, password):
            return None

        async def send_post(self, text):
            return FakePost()

    monkeypatch.setattr(
        bluesky,
        "AsyncClient",
        FakeClient,
    )

    monkeypatch.setattr(
        bluesky.settings,
        "bluesky_handle",
        "example.bsky.social",
    )
    monkeypatch.setattr(
        bluesky.settings,
        "bluesky_app_password",
        "fake-password",
    )

    monkeypatch.setattr(
        platform,
        "verify_public_access",
        AsyncMock(return_value=False),
    )

    result = await platform.publish(
        "Check out our platform https://example.com"
    )

    assert result["status"] == "success"
    assert result["public_access"] is False
    assert result["posted_url"].endswith("/post/abc")
