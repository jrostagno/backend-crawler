import time

import httpx
from bs4 import BeautifulSoup

from app.core.settings import settings


class AmazonClient:
    """Client responsible for fetching Amazon product content."""

    def fetch_description(self, url: str) -> str:
        """Fetch an Amazon page and extract description-like sections."""
        html = self._fetch_html(url)
        return self._extract_description(html)

    def _fetch_html(self, url: str) -> str:
        headers = {"User-Agent": settings.crawl_user_agent}
        last_error: Exception | None = None

        for attempt in range(settings.request_retries + 1):
            try:
                response = httpx.get(
                    url,
                    timeout=settings.crawl_timeout_seconds,
                    headers=headers,
                    follow_redirects=True,
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as error:
                last_error = error
                if attempt < settings.request_retries:
                    time.sleep(0.2 * (attempt + 1))

        raise RuntimeError(f"Failed to fetch Amazon page: {last_error}")

    def _extract_description(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Amazon can move description content across modules; gather from multiple targets.
        selectors = [
            "#productDescription",
            "#feature-bullets",
            "#bookDescription_feature_div",
            "#aplus_feature_div",
            "#dpx-product-description_feature_div",
        ]

        snippets: list[str] = []
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = node.get_text(" ", strip=True)
                if text:
                    snippets.append(text)

        if not snippets:
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc and meta_desc.get("content"):
                snippets.append(str(meta_desc["content"]))

        return " ".join(snippets)
