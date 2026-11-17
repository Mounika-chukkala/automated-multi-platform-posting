
import pytest

from app.platforms.tumblr import TumblrPlatform


def test_tumblr_verification_failure_returns_false(monkeypatch):
    platform = TumblrPlatform()

    monkeypatch.setattr(
        "app.platforms.tumblr.settings.tumblr_client_id",
        "fake-client-id"
    )

    def mock_request(request):
        raise RuntimeError("Tumblr API unavailable")

    monkeypatch.setattr(platform, "_make_request", mock_request)

    result = platform._verify_public_access(
        blog_identifier="example",
        post_id="12345",
        access_token="fake-token"
    )

    assert result is False
