
import asyncio
import json

from app.platforms.devto import DevToPlatform


async def main():
    devto = DevToPlatform()

    message = (
        "Testing automated publishing with DEV.to! "
        "https://example.com"
    )

    result = await devto.publish(message)

    print("\nDEV.to publishing result:")
    print(json.dumps(result, indent=4, default=str))


if __name__ == "__main__":
    asyncio.run(main())
