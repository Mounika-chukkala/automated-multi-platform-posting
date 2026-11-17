
import asyncio
import httpx

from app.config import settings


async def main():
    if not settings.devto_api_key:
        print("DEV.to API key is missing.")
        return

    headers = {
        "api-key": settings.devto_api_key,
        "Accept": "application/vnd.forem.api-v1+json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "https://dev.to/api/users/me",
            headers=headers,
        )

    print("HTTP Status:", response.status_code)

    if response.status_code == 200:
        user = response.json()
        print("Authentication successful!")
        print("Username:", user.get("username"))
        print("Name:", user.get("name"))
    else:
        print("Authentication failed.")
        print("Response:", response.text)


if __name__ == "__main__":
    asyncio.run(main())
