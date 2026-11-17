
import pytest
from pydantic import ValidationError

from app.schemas import PostingRequest


def test_valid_message_is_accepted():
    request = PostingRequest(
        message="Check out our platform https://example.com"
    )
    assert request.message == "Check out our platform https://example.com"


def test_whitespace_only_message_is_rejected():
    with pytest.raises(ValidationError):
        PostingRequest(message="   ")


def test_message_over_200_characters_is_rejected():
    with pytest.raises(ValidationError):
        PostingRequest(message="x" * 201)


def test_message_without_link_is_rejected():
    with pytest.raises(ValidationError):
        PostingRequest(message="Check out our latest platform")


def test_message_with_two_links_is_rejected():
    with pytest.raises(ValidationError):
        PostingRequest(
            message="Visit https://example.com and https://google.com"
        )


def test_invalid_url_is_rejected():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://not-a-domain")


def test_message_with_exactly_200_characters_is_accepted():
    url = "https://example.com"
    message = ("x" * (200 - len(url) - 1)) + " " + url

    assert len(message) == 200
    request = PostingRequest(message=message)
    assert len(request.message) == 200

@pytest.mark.parametrize(
    "url",
    [
        "https://example.com:invalid",
        "https://example.com:99999",
        "https://.example.com",
    ],
)
def test_malformed_urls_are_rejected(url):
    with pytest.raises(ValidationError):
        PostingRequest(message=f"Check this out: {url}")
