
import logging
import re
from html import unescape
from urllib.parse import quote, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DocQueryAI/1.0)"
}

TIMEOUT = 10
MAX_PAGE_CHARS = 5000


def _clean_text(value):
    value = BeautifulSoup(
        unescape(value or ""), "html.parser"
    ).get_text(" ", strip=True)
    return re.sub(r"\s+", " ", value).strip()


def _normalise_url(url):
    if not isinstance(url, str):
        return ""

    url = url.strip()
    if not url.startswith(("https://", "http://")):
        return ""

    parsed = urlparse(url)
    if not parsed.netloc or any(char.isspace() for char in url):
        return ""

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") or "/",
        "",
        parsed.query,
        "",
    ))


def _extract_page_text(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

        if "text/html" not in response.headers.get(
            "Content-Type", ""
        ).lower():
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "nav", "footer",
            "header", "aside", "form", "noscript"
        ]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.body
        if not main:
            return ""

        blocks = []
        seen = set()

        for tag in main.find_all(["h1", "h2", "h3", "p", "li"]):
            text = _clean_text(tag.get_text(" ", strip=True))

            if len(text) < 35 or text.lower() in seen:
                continue

            seen.add(text.lower())
            blocks.append(text)

        return "\n".join(blocks)[:MAX_PAGE_CHARS]

    except Exception:
        logger.debug("Could not fetch webpage: %s", url, exc_info=True)
        return ""


def _add_result(results, seen_urls, title, url, snippet):
    title = _clean_text(title)
    url = _normalise_url(url)
    snippet = _clean_text(snippet)

    if not title or not url or url in seen_urls:
        return

    seen_urls.add(url)

    # Prefer webpage text; use the search excerpt if blocked.
    content = _extract_page_text(url) or snippet

    if content:
        results.append({
            "title": title,
            "url": url,
            "text": content[:MAX_PAGE_CHARS],
        })


def search_web(query, max_results=3):
    query = (query or "").strip()
    if not query:
        return []

    max_results = max(1, min(int(max_results), 10))
    results = []
    seen_urls = set()

    try:
        with DDGS(timeout=TIMEOUT) as ddgs:
            for item in ddgs.text(
                query,
                max_results=max_results * 2,
            ):
                _add_result(
                    results,
                    seen_urls,
                    item.get("title"),
                    item.get("href"),
                    item.get("body"),
                )

                if len(results) >= max_results:
                    break

    except Exception:
        logger.exception("General web search failed")

    # Wikipedia supplements general results when needed.
    if len(results) < max_results:
        try:
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": max_results * 2,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            items = response.json().get(
                "query", {}
            ).get("search", [])

            for item in items:
                title = _clean_text(item.get("title"))
                url = (
                    "https://en.wikipedia.org/wiki/"
                    + quote(title.replace(" ", "_"))
                )

                _add_result(
                    results,
                    seen_urls,
                    title,
                    url,
                    item.get("snippet"),
                )

                if len(results) >= max_results:
                    break

        except Exception:
            logger.exception("Wikipedia search failed")

    return results[:max_results]
