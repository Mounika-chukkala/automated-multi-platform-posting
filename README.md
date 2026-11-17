# Automated Multi-Platform Posting API

A Python FastAPI application that publishes a single message containing a call-to-action (CTA) link across five social publishing platforms through one REST API endpoint.

The application handles platform authentication, publishing, independent error handling, and public-access verification.

## Features

- Publish a message to five platforms through one API request.
- Validate messages before publishing.
- Enforce a maximum message length of 200 characters.
- Require exactly one valid HTTP or HTTPS CTA link.
- Execute publishing operations concurrently.
- Handle failures independently for each platform.
- Return a standardized result for every platform.
- Verify whether published content is publicly accessible.
- Support OAuth authentication for WordPress and Tumblr.
- Keep credentials in environment variables rather than source code.

## Supported Platforms

| Platform | Authentication | Publishing |
|---|---|---|
| Bluesky | Handle and App Password | AT Protocol |
| Mastodon | Instance URL and Access Token | REST API |
| WordPress.com | OAuth 2.0 | WordPress REST API |
| Tumblr | OAuth 2.0 | Tumblr API v2 |
| DEV.to | API Key | DEV Community API |

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Validation:** Pydantic
- **HTTP Client:** HTTPX
- **Other Libraries:** AT Protocol, Requests/urllib, python-dotenv
- **Testing:** Pytest and pytest-asyncio

## Project Structure

```text
automated-multi-platform-posting/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   │
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── bluesky.py
│   │   ├── mastodon.py
│   │   ├── wordpress.py
│   │   ├── tumblr.py
│   │   └── devto.py
│   │
│   └── services/
│       ├── __init__.py
│       └── posting_service.py
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_bluesky.py
│   ├── test_mastodon.py
│   ├── test_posting_service.py
│   ├── test_schemas.py
│   ├── test_tumblr_adapter.py
│   └── test_wordpress.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mounika-chukkala/automated-multi-platform-posting.git
cd automated-multi-platform-posting
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

```env
# Bluesky
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_APP_PASSWORD=your_generated_app_password

# Mastodon
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_mastodon_access_token

# WordPress
WORDPRESS_CLIENT_ID=your_wordpress_client_id
WORDPRESS_CLIENT_SECRET=your_wordpress_client_secret
WORDPRESS_ACCESS_TOKEN=
WORDPRESS_SITE_URL=https://your-site.wordpress.com

# Tumblr
TUMBLR_CLIENT_ID=your_tumblr_client_id
TUMBLR_CLIENT_SECRET=your_tumblr_client_secret
TUMBLR_ACCESS_TOKEN=
TUMBLR_REFRESH_TOKEN=
TUMBLR_BLOG_IDENTIFIER=

# DEV.to
DEVTO_API_KEY=your_devto_api_key
```

Replace the placeholder values with your actual credentials.

**Important:** Never commit your `.env` file or expose API keys, access tokens, client secrets, or passwords publicly.

### 5. Authenticate WordPress and Tumblr

The application provides OAuth login and callback endpoints.

Start the server and open these URLs in your browser:

**WordPress:**

```text
http://localhost:4000/wordpress/login
```

**Tumblr:**

```text
http://localhost:4000/tumblr/login
```

Complete the authorization process in your browser.

The application saves the returned credentials to the local `.env` file.

Before authentication, configure the corresponding client ID and client secret. The OAuth application's registered redirect URI must match the application's callback URL:

- WordPress: `http://localhost:4000/wordpress/callback`
- Tumblr: `http://localhost:4000/tumblr/callback`

The WordPress site URL must also be configured before starting authentication.

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

The application will be available at:

- **API Base URL:** http://localhost:4000
- **Swagger UI:** http://localhost:4000/docs
- **ReDoc:** http://localhost:4000/redoc
- **Health Check:** http://localhost:4000/health

## API Documentation

### POST /posting

Publishes the supplied message to all five configured platforms.

**Endpoint:**

```http
POST http://localhost:4000/posting
```

**Request Headers:**

```http
Content-Type: application/json
```

**Request Body:**

```json
{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

### Validation Rules

The API validates the incoming message before initiating publishing.

- The message must not be empty or contain only whitespace.
- The message must not exceed 200 characters.
- Exactly one HTTP or HTTPS CTA link is required.
- The URL must have a valid hostname.
- Invalid URL structures and ports are rejected.

Invalid requests receive a validation error response from FastAPI.

### Response Format

The API returns a result for each platform under the `results` field.

**Example successful response:**

```json
{
  "results": [
    {
      "platform": "Bluesky",
      "status": "success",
      "posted_url": "https://bsky.app/profile/example.bsky.social/post/123",
      "public_access": true,
      "date": "2026-11-17",
      "time": "06:30:00",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@example/123",
      "public_access": true,
      "date": "2026-11-17",
      "time": "06:30:01",
      "error": null
    },
    {
      "platform": "WordPress",
      "status": "success",
      "posted_url": "https://example.wordpress.com/123",
      "public_access": true,
      "date": "2026-11-17",
      "time": "06:30:02",
      "error": null
    },
    {
      "platform": "Tumblr",
      "status": "success",
      "posted_url": "https://example.tumblr.com/post/123",
      "public_access": true,
      "date": "2026-11-17",
      "time": "06:30:03",
      "error": null
    },
    {
      "platform": "DEV.to",
      "status": "success",
      "posted_url": "https://dev.to/example/article",
      "public_access": true,
      "date": "2026-11-17",
      "time": "06:30:04",
      "error": null
    }
  ]
}
```

*The response above is illustrative. Actual URLs, timestamps, and publishing statuses depend on the platform API responses.*

### Response Fields

| Field | Description |
|---|---|
| `platform` | Name of the publishing platform |
| `status` | Publishing status: `success` or `failed` |
| `posted_url` | URL of the published content, or null if publishing failed |
| `public_access` | Whether public accessibility was verified |
| `date` | Publishing result date |
| `time` | Publishing result time |
| `error` | Error description, or null if no publishing error occurred |

**Note:** A platform can return `status: success` with `public_access: false`. This means the publishing operation succeeded, but public accessibility could not be independently verified.

## Error Handling

Each platform is processed independently.

The application uses asynchronous execution to publish to all platforms concurrently. If one platform fails due to missing credentials, an API error, or a connection issue, the other platform operations continue.

Failed operations return a standardized result containing:

- Platform name
- Failed status
- Null posted URL
- Public-access status set to false
- Date and time
- Error description

## Running Tests

The project uses Pytest for automated testing.

Run the complete test suite:

```bash
pytest -v
```

The test suite covers:

- Request validation
- Message length and CTA URL validation
- API endpoint behavior
- Independent platform failure handling
- Platform publishing and public-access verification scenarios

## API References

The integrations use the respective platform APIs:

- [Bluesky Developer Documentation](https://docs.bsky.app/)
- [Mastodon API Documentation](https://docs.joinmastodon.org/methods/statuses/)
- [WordPress.com REST API Documentation](https://developer.wordpress.com/docs/api/)
- [Tumblr API Documentation](https://www.tumblr.com/docs/en/api/v2)
- [DEV.to API Documentation](https://developers.forem.com/api)

## Security Notes

- Credentials are loaded through environment variables.
- The `.env` file is excluded from Git using `.gitignore`.
- `.env.example` provides placeholder configuration values.
- OAuth state values are validated during WordPress and Tumblr callback handling.

## Author

**Mounika Chukkala**

GitHub: [Mounika-chukkala](https://github.com/Mounika-chukkala)

Repository: [Automated Multi-Platform Posting API](https://github.com/Mounika-chukkala/automated-multi-platform-posting)
