
import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone

from app.config import settings
from app.platforms.base import BasePlatform


class TumblrPlatform(BasePlatform):

    API_BASE_URL = "https://api.tumblr.com/v2"

    @property
    def platform_name(self) -> str:
        return "Tumblr"

    def _make_request(self, request):
        """Execute a Tumblr API request using urllib."""

        try:
            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(
                "utf-8",
                errors="replace"
            )
            raise RuntimeError(
                f"Tumblr API error ({exc.code}): {error_body}"
            )

        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Tumblr connection error: {exc.reason}"
            )


    def _verify_public_access(
    self,
    blog_identifier: str,
    post_id: str,
    access_token: str
    ) -> bool:
        """
    Verify publication using Tumblr's public Posts API.
    This endpoint requires an API key, not a Bearer token.
    """

        query_params = urllib.parse.urlencode({
        "id": post_id,
        "api_key": settings.tumblr_client_id,
    })

        verification_url = (
        f"{self.API_BASE_URL}/blog/"
        f"{urllib.parse.quote(blog_identifier, safe='')}"
        f"/posts?{query_params}"
    )
 
        verification_request = urllib.request.Request(
            verification_url,
        headers={
            "User-Agent": "AutomatedMultiPlatformPosting/1.0",
        },
        method="GET",
    )
 
        try:
            verification_data = self._make_request(
            verification_request
        )

            posts = (
            verification_data
            .get("response", {})
            .get("posts", [])
        )

            return any(
            str(post.get("id_string") or post.get("id"))
            == str(post_id)
            and post.get("state") == "published"
            for post in posts
        )

        except Exception as exc:
            print(f"Tumblr verification warning: {exc}")
            return False


    def _publish_sync(self, message: str) -> dict:

        access_token = settings.tumblr_access_token
        blog_identifier = settings.tumblr_blog_identifier

        if not access_token:
            raise ValueError(
                "Tumblr access token is not configured."
            )

        if not blog_identifier:
            raise ValueError(
                "Tumblr blog identifier is not configured."
            )

        # Step 1: Publish the post.
        publish_url = (
            f"{self.API_BASE_URL}/blog/"
            f"{urllib.parse.quote(blog_identifier, safe='')}"
            f"/post"
        )

        post_data = urllib.parse.urlencode({
            "type": "text",
            "body": message,
            "state": "published",
        }).encode("utf-8")

        publish_request = urllib.request.Request(
            publish_url,
            data=post_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "AutomatedMultiPlatformPosting/1.0",
            },
            method="POST",
        )

        result = self._make_request(publish_request)

        response_data = result.get("response", {})

        post_id = (
            response_data.get("id_string")
            or response_data.get("id")
        )

        if not post_id:
            raise RuntimeError(
                f"Tumblr did not return a post ID: {result}"
            )

        # Step 2: Construct the post URL.
        post_url = (
            response_data.get("post_url")
            or (
                f"https://{blog_identifier}.tumblr.com/"
                f"post/{post_id}"
            )
        )

        # Step 3: Verify publication independently.
        public_access = self._verify_public_access(
            blog_identifier,
            str(post_id),
            access_token
        )

        # Step 4: Prepare the standard result.
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

    async def publish(self, message: str) -> dict:

        return await asyncio.to_thread(
            self._publish_sync,
            message
        )
