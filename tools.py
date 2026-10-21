import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from langchain.tools import tool
from pydantic import BaseModel, Field
import requests
from tavily import TavilyClient

from config import SCRAPE_CHARS

logger = logging.getLogger(__name__)


def _get_tavily():
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is missing. Add it to your .env file.")
    return TavilyClient(api_key=key)


class WebSearchInput(BaseModel):
    query: str = Field(
        description="The search query string to look up on the web (e.g. 'autonomous humanoid robots 2026')"
    )


@tool("web_search", args_schema=WebSearchInput)
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns Titles, URLs, scores and snippets."""
    try:
        results = _get_tavily().search(query=query, max_results=5)
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return f"Search failed: {str(e)}"

    items = results.get("results", [])
    # Sort results by Tavily relevance score descending
    items.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)

    out = []
    for r in items:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        score = float(r.get("score", 0.0))
        snippet = (r.get("content") or "")[:300]
        out.append(
            f"Title: {title}\nURL: {url}\nScore: {score:.4f}\nSnippet: {snippet}\n"
        )

    return "\n----\n".join(out)


def _scrape(url: str, limit: int = SCRAPE_CHARS) -> str:
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text)[:limit]
    except Exception as e:
        logger.warning("Could not scrape %s: %s", url, e)
        return f"Could not scrape URL: {str(e)}"


def scrape_many(urls, limit: int = SCRAPE_CHARS) -> dict:
    """Scrape several URLs in parallel. Returns {url: text}."""
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=min(4, len(urls))) as ex:
        texts = list(ex.map(lambda u: _scrape(u, limit), urls))
    return dict(zip(urls, texts))
