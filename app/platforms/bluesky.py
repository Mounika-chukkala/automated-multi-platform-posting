
from atproto import AsyncClient

from app.config import settings
from app.platforms.base import BasePlatform
import httpx
from datetime import datetime, timezone
class BlueskyPlatform(BasePlatform):

    @property
    def platform_name(self) -> str:
        return "Bluesky"

    async def verify_public_access(self, post_uri: str) -> bool:
        endpoint = (
            "https://public.api.bsky.app/xrpc/"
            "app.bsky.feed.getPostThread"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    endpoint,
                    params={
                        "uri": post_uri,
                        "depth": 0
                    }
                )

                response.raise_for_status()

                data = response.json()
                verified_uri = (
                    data.get("thread", {})
                    .get("post", {})
                    .get("uri")
                )

                return verified_uri == post_uri

        except (httpx.HTTPError, ValueError):
            return False

    async def publish(self, message: str) -> dict:

        # Check whether credentials are configured
        if not settings.bluesky_handle or not settings.bluesky_app_password:
            raise RuntimeError("Bluesky credentials are not configured.")

        # Create an asynchronous Bluesky client
        client = AsyncClient()

        try:
            # Authenticate with the Bluesky account
            await client.login(
                settings.bluesky_handle,
                settings.bluesky_app_password
            )

            # Publish the message
            post = await client.send_post(text=message)

            # Extract the post identifier
            post_id = post.uri.rsplit("/", 1)[-1]

            # Construct the public post URL
            posted_url = (
                f"https://bsky.app/profile/"
                f"{settings.bluesky_handle}/post/{post_id}"
            )
            now = datetime.now(timezone.utc)
            public_access = await self.verify_public_access(post.uri)
            return {
                 "platform": self.platform_name,
    "status": "success",
    "posted_url": posted_url,
    "public_access": public_access,
    "date": now.date(),
    "time": now.time().replace(microsecond=0, tzinfo=None),
    "error": None
            }

        except Exception as exc:
            raise RuntimeError(
                f"Bluesky publishing failed: {exc}"
            ) from exc
