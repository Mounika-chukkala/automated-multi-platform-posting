
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.platforms.base import BasePlatform


class WordPressPlatform(BasePlatform):

    @property
    def platform_name(self):
        return "WordPress"

    def get_site_identifier(self):
        parsed = urlparse(settings.wordpress_site_url)
        return parsed.netloc or parsed.path

    async def verify_public_access(self, post_id):
        site = self.get_site_identifier()

        url = (
            f"https://public-api.wordpress.com/rest/v1.1/"
            f"sites/{site}/posts/{post_id}"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        post = response.json()

        return post.get("status") == "publish" and bool(post.get("URL"))

    async def publish(self, message):
        if not settings.wordpress_access_token:
            raise ValueError("WordPress access token is not configured.")

        if not settings.wordpress_site_url:
            raise ValueError("WordPress site URL is not configured.")

        site = self.get_site_identifier()

        url = (
            f"https://public-api.wordpress.com/rest/v1.1/"
            f"sites/{site}/posts/new"
        )

        headers = {
            "Authorization": (
                f"Bearer {settings.wordpress_access_token}"
            )
        }

        data = {
            "title": "Automated Platform Update",
            "content": message,
            "status": "publish"
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers=headers,
                data=data
            )
            response.raise_for_status()

        post = response.json()

        post_id = post.get("ID")
        posted_url = post.get("URL")

        if not post_id or not posted_url:
            raise ValueError(
                "WordPress did not return a valid post ID or URL."
            )

        public_access = await self.verify_public_access(post_id)

        published_at = datetime.now(timezone.utc)

        return {
            "platform": self.platform_name,
            "status": "success",
            "posted_url": posted_url,
            "public_access": public_access,
            "date": published_at.date(),
            "time": published_at.time().replace(tzinfo=None),
            "error": None
        }
