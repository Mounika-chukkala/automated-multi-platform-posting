
import asyncio
import json
import secrets
import urllib.error
import urllib.request
import uuid

from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from dotenv import set_key
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import settings
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.tumblr import TumblrPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.wordpress import WordPressPlatform
from app.schemas import PostingRequest
from app.services.posting_service import publish_to_all_platforms


app = FastAPI(
    title="Automated Multi-Platform Posting API",
    description="Publish messages to multiple platforms through one API.",
    version="1.0.0",
)


# --------------------------------------------------
# OAuth configuration
# --------------------------------------------------

WORDPRESS_AUTHORIZE_URL = (
    "https://public-api.wordpress.com/oauth2/authorize"
)
WORDPRESS_TOKEN_URL = (
    "https://public-api.wordpress.com/oauth2/token"
)
WORDPRESS_REDIRECT_URI = (
    "http://localhost:4000/wordpress/callback"
)

TUMBLR_AUTHORIZE_URL = (
    "https://www.tumblr.com/oauth2/authorize"
)
TUMBLR_TOKEN_URL = (
    "https://api.tumblr.com/v2/oauth2/token"
)
TUMBLR_REDIRECT_URI = (
    "http://localhost:4000/tumblr/callback"
)


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def save_to_env(key: str, value: str) -> None:
    """Save an OAuth credential to the local .env file."""
    set_key(".env", key, value)


def get_tumblr_user_info(access_token: str) -> dict:
    """
    Retrieve the authenticated Tumblr user's information.

    Uses urllib because HTTPX was failing to connect
    to Tumblr's API in the current development environment.
    """

    request = urllib.request.Request(
        "https://api.tumblr.com/v2/user/info",
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AutomatedMultiPlatformPosting/1.0",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def exchange_tumblr_code_for_token(code: str) -> dict:
    """
    Exchange a Tumblr authorization code for OAuth tokens.

    Uses urllib and multipart form-data.
    """

    boundary = f"----TumblrBoundary{uuid.uuid4().hex}"

    fields = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.tumblr_client_id,
        "client_secret": settings.tumblr_client_secret,
        "redirect_uri": TUMBLR_REDIRECT_URI,
    }

    body_parts = []

    for key, value in fields.items():
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n'
            f"\r\n"
            f"{value}\r\n"
        )

    body_parts.append(f"--{boundary}--\r\n")

    request_body = "".join(body_parts).encode("utf-8")

    request = urllib.request.Request(
        TUMBLR_TOKEN_URL,
        data=request_body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "AutomatedMultiPlatformPosting/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


# --------------------------------------------------
# Basic routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Automated Multi-Platform Posting API is running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# WordPress OAuth
# --------------------------------------------------

@app.get("/wordpress/login")
async def wordpress_login():

    if not settings.wordpress_client_id:
        raise HTTPException(
            status_code=500,
            detail="WordPress client ID is not configured."
        )

    state = secrets.token_urlsafe(32)
    app.state.wordpress_oauth_state = state

    params = {
        "client_id": settings.wordpress_client_id,
        "redirect_uri": WORDPRESS_REDIRECT_URI,
        "response_type": "code",
        "scope": "posts",
        "state": state,
        "blog": settings.wordpress_site_url,
    }

    authorization_url = (
        f"{WORDPRESS_AUTHORIZE_URL}?{urlencode(params)}"
    )

    return RedirectResponse(authorization_url)


@app.get("/wordpress/callback")
async def wordpress_callback(
    code: str = Query(...),
    state: str = Query(...)
):

    expected_state = getattr(
        app.state,
        "wordpress_oauth_state",
        None
    )

    if not expected_state or not secrets.compare_digest(
        state,
        expected_state
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired WordPress OAuth state."
        )

    app.state.wordpress_oauth_state = None

    token_data = {
        "client_id": settings.wordpress_client_id,
        "client_secret": settings.wordpress_client_secret,
        "redirect_uri": WORDPRESS_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                WORDPRESS_TOKEN_URL,
                data=token_data
            )

        response.raise_for_status()
        token_response = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"WordPress token exchange failed: {exc.response.text}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"WordPress OAuth error: {str(exc)}"
        )

    access_token = token_response.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="WordPress did not return an access token."
        )

    save_to_env("WORDPRESS_ACCESS_TOKEN", access_token)

    # Update the in-memory settings as well.
    settings.wordpress_access_token = access_token

    return {
        "message": "WordPress authentication successful.",
        "token_saved": True,
        "site": settings.wordpress_site_url,
    }


# --------------------------------------------------
# Tumblr OAuth
# --------------------------------------------------

@app.get("/tumblr/login")
async def tumblr_login():

    if not settings.tumblr_client_id:
        raise HTTPException(
            status_code=500,
            detail="Tumblr client ID is not configured."
        )

    state = secrets.token_urlsafe(32)
    app.state.tumblr_oauth_state = state

    params = {
        "client_id": settings.tumblr_client_id,
        "response_type": "code",
        "scope": "basic write offline_access",
        "state": state,
        "redirect_uri": TUMBLR_REDIRECT_URI,
    }

    authorization_url = (
        f"{TUMBLR_AUTHORIZE_URL}?{urlencode(params)}"
    )

    return RedirectResponse(authorization_url)


@app.get("/tumblr/callback")
async def tumblr_callback(
    code: str = Query(...),
    state: str = Query(...)
):

    expected_state = getattr(
        app.state,
        "tumblr_oauth_state",
        None
    )

    if not expected_state or not secrets.compare_digest(
        state,
        expected_state
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Tumblr OAuth state."
        )

    app.state.tumblr_oauth_state = None

    if not settings.tumblr_client_id or not settings.tumblr_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Tumblr OAuth credentials are not configured."
        )

    # Step 1: Exchange authorization code for tokens.
    try:
        token_response = await asyncio.to_thread(
            exchange_tumblr_code_for_token,
            code
        )

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        raise HTTPException(
            status_code=400,
            detail=f"Tumblr token exchange failed: {error_body}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Tumblr token exchange error: {str(exc)}"
        )

    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Tumblr did not return an access token."
        )

    # Step 2: Retrieve authenticated Tumblr user information.
    try:
        user_info = await asyncio.to_thread(
            get_tumblr_user_info,
            access_token
        )

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        raise HTTPException(
            status_code=400,
            detail=f"Could not retrieve Tumblr account information: {error_body}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Tumblr user information request failed: {str(exc)}"
        )

    # Step 3: Extract the user's blogs.
    blogs = (
        user_info
        .get("response", {})
        .get("user", {})
        .get("blogs", [])
    )

    if not blogs:
        raise HTTPException(
            status_code=400,
            detail="No Tumblr blogs were found for this account."
        )

    blog_identifier = blogs[0].get("name")

    if not blog_identifier:
        raise HTTPException(
            status_code=400,
            detail="Could not identify the Tumblr blog."
        )

    # Step 4: Save credentials locally.
    save_to_env("TUMBLR_ACCESS_TOKEN", access_token)

    if refresh_token:
        save_to_env("TUMBLR_REFRESH_TOKEN", refresh_token)

    save_to_env(
        "TUMBLR_BLOG_IDENTIFIER",
        blog_identifier
    )

    # Update in-memory settings.
    settings.tumblr_access_token = access_token
    settings.tumblr_blog_identifier = blog_identifier

    if refresh_token:
        settings.tumblr_refresh_token = refresh_token

    return {
        "message": "Tumblr authentication successful.",
        "token_saved": True,
        "blog_identifier": blog_identifier,
    }


# --------------------------------------------------
# Main publishing endpoint
# --------------------------------------------------

@app.post("/posting")
async def create_post(request: PostingRequest):

    platforms = [
        BlueskyPlatform(),
        MastodonPlatform(),
        WordPressPlatform(),
        TumblrPlatform(),
        DevToPlatform(),
    ]

    results = await publish_to_all_platforms(
        platforms,
        request.message
    )

    return {
        "results": results
    }