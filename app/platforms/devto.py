
import httpx

from datetime import datetime, timezone

from app.config import settings
from app.platforms.base import BasePlatform


class DevToPlatform(BasePlatform):

    API_URL = "https://dev.to/api"

    @property
    def platform_name(self) -> str:
        return "DEV.to"

    async def publish(self, message: str) -> dict:

        if not settings.devto_api_key:
            raise ValueError("DEV.to API key is not configured.")

        headers = {
            "api-key": settings.devto_api_key,
            "Accept": "application/vnd.forem.api-v1+json",
            "Content-Type": "application/json",
        }

        unique_title = (
    f"Automated Platform Update "
    f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
)

        article_data = {
    "article": {
        "title": unique_title,
        "body_markdown": message,
        "published": True,
    }
}

        async with httpx.AsyncClient(timeout=30) as client:

            # Publish the article.
            response = await client.post(
                f"{self.API_URL}/articles",
                headers=headers,
                json=article_data,
            )

            if response.status_code != 201:
                raise RuntimeError(
                    f"DEV.to publishing failed: "
                    f"{response.status_code} - {response.text}"
                )

            article = response.json()

            post_url = article.get("url")
            article_id = article.get("id")

            if not post_url or not article_id:
                raise RuntimeError(
                    f"DEV.to did not return article details: {article}"
                )

            # Verify public accessibility without authentication.
            public_access = False

            try:
                verification = await client.get(
                post_url,
                timeout=10.0
                )

                public_access = verification.status_code == 200

            except (httpx.HTTPError, ValueError):
                public_access = False

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
            "error": None,
        }
