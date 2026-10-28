import sys
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, "scripts")

from classify_linkedin_media import fetch_posts

posts = fetch_posts(limit=20)

for index in [1, 11]:  # Posts 02 and 12
    post = posts[index]

    response = requests.get(
        post["post_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    soup = BeautifulSoup(response.text, "html.parser")

    canonical = soup.find(
        "link",
        rel="canonical"
    )

    print(f"\nPOST {index + 1:02d}")
    print("Database URL:", post["post_url"])
    print(
        "Canonical URL:",
        canonical.get("href") if canonical else "Not found"
    )