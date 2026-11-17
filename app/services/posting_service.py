
import asyncio
from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


async def publish_to_one_platform(
    platform: BasePlatform,
    message: str
) -> PlatformResult:

    try:
        result = await platform.publish(message)

        return PlatformResult.model_validate(result)

    except Exception as exc:
        now = datetime.now(timezone.utc)

        return PlatformResult(
            platform=platform.platform_name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=now.date(),
            time=now.time().replace(microsecond=0, tzinfo=None),
            error=str(exc)
        )


async def publish_to_all_platforms(
    platforms: list[BasePlatform],
    message: str
) -> list[PlatformResult]:

    tasks = [
        publish_to_one_platform(platform, message)
        for platform in platforms
    ]

    results = await asyncio.gather(*tasks)

    return results
