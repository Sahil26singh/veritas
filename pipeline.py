import logging
import re
import sys
import time
from urllib.parse import urlparse
import groq

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents import writer_chain, critic_chain
from tools import web_search, scrape_many
from config import MAX_URLS, SCRAPE_CHARS, CRITIC_SOURCE_CHARS, REVISE_BELOW

logger = logging.getLogger(__name__)


def extract_urls(text: str) -> list[str]:
    """Extract unique http(s) URLs found in text, in order."""
    urls = re.findall(r"https?://[^\s\)\]\"'<>]+", text)
    seen = set()
    out = []
    for u in urls:
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def dedupe_by_domain(urls: list[str]) -> list[str]:
    """Deduplicate URLs preserving first occurrence per domain (netloc)."""
    seen_domains = set()
    deduped = []
    for u in urls:
        parsed = urlparse(u)
        domain = parsed.netloc.lower()
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            deduped.append(u)
        elif not domain and u not in deduped:
            deduped.append(u)
    return deduped


def build_source_blocks(research: str) -> tuple[str, str]:
    """Parse research into numbered sources ([1], [2], ...) for writer and critic.

    Omit snippets from search results for any URL that was scraped.
    Returns (writer_sources, critic_sources).
    """
    # 1. Parse scraped pages
    scraped_entries = []
    scraped_pattern = re.compile(r"SOURCE:\s*(https?://[^\s\n]+)\n(.*?)(?=(?:\n\nSOURCE:|$))", re.DOTALL)
    for m in scraped_pattern.finditer(research):
        url = m.group(1).strip()
        body = m.group(2).strip()
        scraped_entries.append((url, body))

    scraped_urls = {u.rstrip(".,;") for u, _ in scraped_entries}

    # 2. Parse search entries
    search_entries = []
    # Search results format: Title: ...\nURL: ...\nScore: ...\nSnippet: ...
    search_pattern = re.compile(
        r"Title:\s*(.*?)\nURL:\s*(https?://[^\s\n]+)(?:\nScore:\s*([^\n]+))?\nSnippet:\s*(.*?)(?=(?:\n----\n|\nTitle:|$))",
        re.DOTALL,
    )
    for m in search_pattern.finditer(research):
        title = m.group(1).strip()
        url = m.group(2).strip().rstrip(".,;")
        score = m.group(3).strip() if m.group(3) else "0.0"
        snippet = m.group(4).strip()
        search_entries.append((url, title, score, snippet))

    # Unified list of numbered sources
    sources_writer = []
    sources_critic = []
    idx = 1
    registered_urls = set()

    # Add scraped sources first (highest fidelity)
    for url, body in scraped_entries:
        clean_url = url.rstrip(".,;")
        registered_urls.add(clean_url)
        writer_text = body[:SCRAPE_CHARS]
        critic_text = body[:CRITIC_SOURCE_CHARS]
        sources_writer.append(f"[{idx}] URL: {clean_url}\nContent: {writer_text}")
        sources_critic.append(f"[{idx}] URL: {clean_url}\nContent: {critic_text}")
        idx += 1

    # Add remaining unscraped search sources (omitting snippets for already scraped URLs)
    for url, title, score, snippet in search_entries:
        clean_url = url.rstrip(".,;")
        if clean_url in registered_urls or clean_url in scraped_urls:
            # Snippet omitted for URLs that were scraped
            continue
        registered_urls.add(clean_url)
        writer_text = f"Title: {title}\nSnippet: {snippet}"
        critic_text = f"Title: {title}\nSnippet: {snippet}"
        sources_writer.append(f"[{idx}] URL: {clean_url}\n{writer_text}")
        sources_critic.append(f"[{idx}] URL: {clean_url}\n{critic_text}")
        idx += 1

    if not sources_writer:
        # Fallback if unformatted text passed
        return research, research[: (CRITIC_SOURCE_CHARS * 2)]

    return "\n\n".join(sources_writer), "\n\n".join(sources_critic)


# ── Step 1: search ────────────────────────────────────────────────────────────
def run_search_step(topic: str):
    """Directly invokes web_search tool without LLM call. Returns (raw, urls)."""
    raw = web_search.invoke({"query": topic})
    if isinstance(raw, str) and raw.startswith("Search failed"):
        raise RuntimeError(raw)
    return raw, extract_urls(raw)


# ── Step 2: reader (scrapes top pages directly, in parallel) ─────────────────
def run_reader_step(urls: list) -> str:
    """Scrapes top pages until MAX_URLS succeed, backfilling from candidates."""
    candidates = dedupe_by_domain(urls)
    good_pages = {}

    idx = 0
    while idx < len(candidates) and len(good_pages) < MAX_URLS:
        batch_size = MAX_URLS - len(good_pages)
        batch = candidates[idx : idx + batch_size]
        idx += batch_size
        scraped = scrape_many(batch, SCRAPE_CHARS)
        for u, text in scraped.items():
            if (
                text
                and not text.startswith("Could not scrape URL:")
                and len(text.strip()) > 50
            ):
                good_pages[u] = text
                if len(good_pages) >= MAX_URLS:
                    break

    if not good_pages:
        return "No pages could be scraped. Rely on the search results only."
    return "\n\n".join(f"SOURCE: {u}\n{t}" for u, t in good_pages.items())


# ── Step 3+4: writer <-> critic loop ─────────────────────────────────────────
def _invoke_with_retry(chain, payload: dict, desc: str = "LLM call", max_attempts: int = 3):
    """Invokes chain with exponential backoff if rate limited by Groq."""
    for attempt in range(1, max_attempts + 1):
        try:
            return chain.invoke(payload)
        except groq.RateLimitError:
            if attempt == max_attempts:
                raise
            wait_time = 2 ** attempt
            logger.warning(
                "[Groq Rate Limit on %s]: Backing off %ss (attempt %s/%s)...",
                desc,
                wait_time,
                attempt,
                max_attempts,
            )
            time.sleep(wait_time)
        except groq.APIStatusError as err:
            if err.status_code in (413, 429) and attempt < max_attempts:
                wait_time = 2 ** attempt
                logger.warning(
                    "[Groq API Status %s on %s]: Backing off %ss (attempt %s/%s)...",
                    err.status_code,
                    desc,
                    wait_time,
                    attempt,
                    max_attempts,
                )
                time.sleep(wait_time)
            else:
                raise
        except Exception:
            raise


def run_writer_critic_loop(topic: str, research: str, on_progress=None):
    """Executes writer -> critic -> optional single revision if score < REVISE_BELOW.

    Returns (report, feedback, rounds).
    """
    writer_sources, critic_sources = build_source_blocks(research)

    if on_progress:
        on_progress("writer")

    report = _invoke_with_retry(
        writer_chain,
        {"topic": topic, "sources": writer_sources},
        desc="Writer (Initial Draft)",
    )

    if on_progress:
        on_progress("critic")

    feedback = _invoke_with_retry(
        critic_chain,
        {"report": report, "sources": critic_sources},
        desc="Critic Evaluation",
    )

    score = getattr(feedback, "score", None)
    if score is None and isinstance(feedback, dict):
        score = feedback.get("score")

    rounds = 1
    if score is not None and score < REVISE_BELOW:
        rounds = 2
        if on_progress:
            on_progress("revision")
        feedback_str = (
            feedback.to_markdown() if hasattr(feedback, "to_markdown") else str(feedback)
        )
        report = _invoke_with_retry(
            writer_chain,
            {
                "topic": topic,
                "sources": writer_sources,
                "previous_draft": report,
                "feedback": feedback_str,
            },
            desc="Writer (Revision Draft)",
        )

    return report, feedback, rounds


def run_research_pipeline(topic: str) -> dict:
    state = {}

    print("\n" + " =" * 50)
    print("Step 1 - Web search is querying Tavily...")
    print("=" * 50)

    state["search_results"], urls = run_search_step(topic)
    print("\nSearch Results:\n", state["search_results"])

    print("\n" + " =" * 50)
    print("Step 2 - Scraping top resources in parallel...")
    print("=" * 50)

    state["scraped_content"] = run_reader_step(urls)
    print("\nScraped Content:\n", state["scraped_content"])

    print("\n" + " =" * 50)
    print("Step 3/4 - Writer drafts, Critic evaluates (revises if score < threshold)...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )

    state["report"], state["feedback"], state["rounds"] = run_writer_critic_loop(
        topic, research_combined
    )

    print("\nFinal Report:\n", state["report"])
    print("\nCritic Evaluation:\n", state["feedback"])
    print(f"\nDrafts Written: {state['rounds']}")

    return state


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    topic_input = input("\nEnter a research topic: ")
    if topic_input.strip():
        run_research_pipeline(topic_input)
