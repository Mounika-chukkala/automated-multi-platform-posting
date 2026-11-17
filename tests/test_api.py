
from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


class FakePlatform:
    def __init__(self, name, should_fail=False):
        self.platform_name = name
        self.should_fail = should_fail

    async def publish(self, message):
        if self.should_fail:
            raise RuntimeError("Simulated platform failure")

        return {
            "platform": self.platform_name,
            "status": "success",
            "posted_url": f"https://example.com/{self.platform_name.lower()}",
            "public_access": True,
            "date": "2026-11-17",
            "time": "10:00:00",
            "error": None,
        }


def setup_fake_platforms(monkeypatch, failing_platform=None):
    platform_names = [
        "Bluesky",
        "Mastodon",
        "WordPress",
        "Tumblr",
        "DEV.to",
    ]

    for name in platform_names:
        fake_class = lambda name=name: FakePlatform(
            name,
            should_fail=(name == failing_platform),
        )

        if name == "Bluesky":
            monkeypatch.setattr(main, "BlueskyPlatform", fake_class)
        elif name == "Mastodon":
            monkeypatch.setattr(main, "MastodonPlatform", fake_class)
        elif name == "WordPress":
            monkeypatch.setattr(main, "WordPressPlatform", fake_class)
        elif name == "Tumblr":
            monkeypatch.setattr(main, "TumblrPlatform", fake_class)
        elif name == "DEV.to":
            monkeypatch.setattr(main, "DevToPlatform", fake_class)


def test_posting_endpoint_returns_five_platform_results(monkeypatch):
    setup_fake_platforms(monkeypatch)

    response = client.post(
        "/posting",
        json={
            "message": "Check out our platform https://example.com"
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 5

    assert all(
        result["status"] == "success"
        for result in data["results"]
    )


def test_posting_endpoint_handles_platform_failure(monkeypatch):
    setup_fake_platforms(
        monkeypatch,
        failing_platform="Tumblr",
    )

    response = client.post(
        "/posting",
        json={
            "message": "Check out our platform https://example.com"
        },
    )

    assert response.status_code == 200

    results = response.json()["results"]

    assert len(results) == 5

    tumblr_result = next(
        result for result in results
        if result["platform"] == "Tumblr"
    )

    assert tumblr_result["status"] == "failed"
    assert tumblr_result["error"] == "Simulated platform failure"

    successful_results = [
        result for result in results
        if result["platform"] != "Tumblr"
    ]

    assert all(
        result["status"] == "success"
        for result in successful_results
    )


def test_posting_endpoint_rejects_invalid_message():
    response = client.post(
        "/posting",
        json={
            "message": "This message has no link"
        },
    )

    assert response.status_code == 422
