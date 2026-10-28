import json
import requests
from bs4 import BeautifulSoup

url = (
    "https://www.linkedin.com/feed/update/"
    "urn%3Ali%3Ashare%3A7518213428709322752"
)

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("\nSTRUCTURED LINKEDIN DATA")
print("=" * 70)

for script in soup.select('script[type="application/ld+json"]'):
    try:
        data = json.loads(script.string or script.get_text())
        print(json.dumps(data, indent=2, ensure_ascii=False)[:8000])
    except (json.JSONDecodeError, TypeError):
        continue

print("\nSOCIAL ACTION ELEMENTS")
print("=" * 70)

article = soup.select_one("article.main-feed-activity-card")

if article:
    social_actions = article.select_one(
        ".main-feed-activity-card__social-actions"
    )

    if social_actions:
        print(social_actions.prettify()[:8000])