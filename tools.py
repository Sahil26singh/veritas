from langchain.tools import tool
import re
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from rich import print
from config import SCRAPE_CHARS
load_dotenv()


def _get_tavily():
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is missing. Add it to your .env file.")
    return TavilyClient(api_key=key)


@tool
def web_search(query : str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    try:
        results = _get_tavily().search(query=query, max_results=5)
    except Exception as e:
        return f"Search failed: {str(e)}"

    out = []

    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )

    return "\n----\n".join(out)


def _scrape(url: str, limit: int = SCRAPE_CHARS) -> str:
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text)[:limit]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    return _scrape(url)


def scrape_many(urls, limit: int = SCRAPE_CHARS) -> dict:
    """Scrape several URLs in parallel. Returns {url: text}."""
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=min(4, len(urls))) as ex:
        texts = list(ex.map(lambda u: _scrape(u, limit), urls))
    return dict(zip(urls, texts))
