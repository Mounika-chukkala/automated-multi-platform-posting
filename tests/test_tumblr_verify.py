
from app.config import settings
from app.platforms.tumblr import TumblrPlatform


def main():
    tumblr = TumblrPlatform()

    post_id = "833448673476296704"

    result = tumblr._verify_public_access(
        blog_identifier=settings.tumblr_blog_identifier,
        post_id=post_id,
        access_token=settings.tumblr_access_token,
    )

    print("Tumblr post ID:", post_id)
    print("API publication verification:", result)


if __name__ == "__main__":
    main()
