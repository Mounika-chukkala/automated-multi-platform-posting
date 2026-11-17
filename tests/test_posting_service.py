
from datetime import date, datetime

import pytest

from app.platforms.base import BasePlatform
from app.services.posting_service import publish_to_all_platforms


class SuccessfulPlatform(BasePlatform):

    @property
    def platform_name(self):
        return "WorkingPlatform"

    async def publish(self, message):
        now = datetime.now()

        return {
            "platform": self.platform_name,
            "status": "success",
            "posted_url": "https://example.com/post/123",
            "public_access": True,
            "date": date.today(),
            "time": now.time().replace(microsecond=0),
            "error": None
        }


class FailingPlatform(BasePlatform):

    @property
    def platform_name(self):
        return "FailingPlatform"

    async def publish(self, message):
        raise Exception("Simulated API failure")


@pytest.mark.asyncio
async def test_one_platform_failure_does_not_stop_others():

    platforms = [
        SuccessfulPlatform(),
        FailingPlatform(),
        SuccessfulPlatform()
    ]

    results = await publish_to_all_platforms(
        platforms,
        "Testing independent failure handling"
    )

    assert len(results) == 3

    assert results[0].status == "success"
    assert results[1].status == "failed"
    assert results[2].status == "success"

    assert results[1].error == "Simulated API failure"

    print("Independent failure handling works!")
