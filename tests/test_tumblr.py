
import asyncio
import json

from app.platforms.tumblr import TumblrPlatform


async def main():
    tumblr = TumblrPlatform()

    message = (
        "Testing automated publishing with Tumblr! "
        "https://example.com"
    )

    result = await tumblr.publish(message)

    print("\nTumblr publishing result:")
    print(json.dumps(result, indent=4, default=str))


if __name__ == "__main__":
    asyncio.run(main())
