from urllib.parse import urlparse, urlunparse
from pydantic import validate_call
from typing import Optional
import re

@validate_call
def remove_query_params_from_url(url: str) -> str:
    parsed_url = urlparse(url)

    clean_url = urlunparse(
        parsed_url._replace(query="")
    )

    return clean_url

@validate_call
def parse_url(url: str, origin_url: str) -> tuple[Optional[str], Optional[str]]:
    id = None
    slug = None

    url = remove_query_params_from_url(url)

    if origin_url.startswith("http://"):
        origin_url = origin_url.replace("http://", "https://")

    elif not origin_url.startswith("https://"):
        origin_url = f"https://{origin_url}"

    if not origin_url.startswith("https://www."):
        origin_url = origin_url.replace("https://", "https://www.")

    if origin_url.endswith("/"):
        origin_url = origin_url.removesuffix("/")

    if url.startswith(origin_url):
        url = url[len(origin_url):]

    if url.startswith("/dp/"):
        match = re.match(r"/dp/([^/]+)/?", url)
        id = match.group(1)

    else:
        match = re.match(r"/(.*?)/dp/([^/]+)/?", url)
        if match:
            slug = match.group(1)
            id = match.group(2)

    return id, slug