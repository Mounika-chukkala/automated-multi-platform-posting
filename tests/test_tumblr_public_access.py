
import urllib.request
import urllib.error

post_url = "https://mounikach178.tumblr.com/post/833448673476296704"

request = urllib.request.Request(
    post_url,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    },
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        print("HTTP status:", response.status)
        print("Final URL:", response.geturl())
        print("Content type:", response.headers.get("Content-Type"))
        print("Public access:", response.status == 200)

except urllib.error.HTTPError as exc:
    print("HTTP error:", exc.code)
    print("Reason:", exc.reason)

except Exception as exc:
    print("Verification error:", repr(exc))
