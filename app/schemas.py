
import re
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

from datetime import date, time
from typing import Literal, Optional


class PostingRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Message to publish, containing exactly one valid URL."
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, message: str) -> str:
        # Reject messages containing only whitespace
        if not message.strip():
            raise ValueError("Message cannot be empty.")

        # Extract HTTP and HTTPS URLs
        urls = re.findall(r"https?://[^\s]+", message)

        # Remove common punctuation attached to URLs
        urls = [url.rstrip(".,!?;:)]}") for url in urls]

        # Exactly one URL is required
        if len(urls) != 1:
            raise ValueError("Message must contain exactly one CTA link.")

        # Validate the URL structure
        parsed_url = urlsplit(urls[0])

        if (
            parsed_url.scheme not in ("http", "https")
            or not parsed_url.hostname
            or "." not in parsed_url.hostname
        ):
            raise ValueError("Please provide a valid HTTP or HTTPS URL.")

        return message





class PlatformResult(BaseModel):
    platform: str

    status: Literal["success", "failed"]

    posted_url: Optional[str] = None

    public_access: bool = False

    date: date

    time: time

    error: Optional[str] = None
