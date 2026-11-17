
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.platforms.base import BasePlatform


class MastodonPlatform(BasePlatform):

    @property
    def platform_name(self) -> str:
        return "Mastodon"

    async def verify_public_access(self, status_id: str) -> bool:
        instance_url = settings.mastodon_instance_url.rstrip("/")
        endpoint = f"{instance_url}/api/v1/statuses/{status_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint)
                response.raise_for_status()

                status_data = response.json()

                return (
                    str(status_data.get("id")) == str(status_id)
                    and status_data.get("visibility") == "public"
                )

        except (httpx.HTTPError, ValueError):
            return False

    async def publish(self, message: str) -> dict:

        if (
            not settings.mastodon_instance_url
            or not settings.mastodon_access_token
        ):
            raise RuntimeError(
                "Mastodon credentials are not configured."
            )

        instance_url = settings.mastodon_instance_url.rstrip("/")
        endpoint = f"{instance_url}/api/v1/statuses"

        headers = {
            "Authorization": f"Bearer {settings.mastodon_access_token}"
        }

        payload = {
            "status": message,
            "visibility": "public"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            post_data = response.json()

        post_url = post_data.get("url")
        status_id = post_data.get("id")

        if not post_url or not status_id:
            raise RuntimeError(
                "Mastodon response is missing the post URL or ID."
            )

        public_access = await self.verify_public_access(status_id)

        now = datetime.now(timezone.utc)

        return {
            "platform": self.platform_name,
            "status": "success",
            "posted_url": post_url,
            "public_access": public_access,
            "date": now.date(),
            "time": now.time().replace(
                microsecond=0,
                tzinfo=None
            ),
            "error": None
        }
