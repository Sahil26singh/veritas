import re
import time
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents import build_search_agent , writer_chain , critic_chain
from tools import web_search , scrape_many
from config import MAX_URLS , SCRAPE_CHARS , MIN_SCORE , MAX_ROUNDS , CRITIC_RESEARCH_CHARS


def _text(msg) -> str:
    """Message content as plain string (some models return a list of blocks)."""
    content = msg.content
    if isinstance(content, list):
        return "".join(
            b if isinstance(b, str) else b.get("text", "") for b in content
        )
    return content or ""


def extract_urls(text: str) -> list:
    """Unique http(s) URLs found in text, in order."""
    urls = re.findall(r"https?://[^\s\)\]\"'<>]+", text)
    seen, out = set(), []
    for u in urls:
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def parse_score(feedback: str):
    """Pull 'Score: X/10' out of the critic text. Returns float or None."""
    m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    return float(m.group(1)) if m else None


# ── Step 1: search ────────────────────────────────────────────────────────────
def run_search_step(topic: str):
    """Returns (search_text, urls)."""
    raw_tool_output = ""
    summary = ""
    try:
        search_agent = build_search_agent()
        result = search_agent.invoke({
            "messages": [("user", f"Use the web_search tool with query='{topic}' to find recent, reliable and detailed information on this topic.")]
        })
        summary = _text(result["messages"][-1])
        # raw tool output holds every URL (agent summary may drop some)
        raw_tool_output = "\n\n".join(
            _text(m) for m in result["messages"] if getattr(m, "type", "") == "tool"
        )
    except Exception as e:
        print(f"search agent failed ({e}); calling web_search directly")

    if not raw_tool_output:
        # fallback: call the tool directly
        raw_tool_output = web_search.invoke({"query": topic})
        if raw_tool_output.startswith("Search failed"):
            raise RuntimeError(raw_tool_output)

    search_text = f"{summary}\n\nRAW SEARCH RESULTS:\n{raw_tool_output}".strip()
    urls = extract_urls(raw_tool_output) or extract_urls(summary)
    return search_text, urls


# ── Step 2: reader (scrapes top pages directly, in parallel) ─────────────────
def run_reader_step(urls: list) -> str:
    pages = scrape_many(urls[:MAX_URLS], SCRAPE_CHARS)
    good = {u: t for u, t in pages.items() if not t.startswith("Could not scrape")}
    if not good:
        return "No pages could be scraped. Rely on the search results only."
    return "\n\n".join(f"SOURCE: {u}\n{t}" for u, t in good.items())


# ── Step 3+4: writer <-> critic loop ─────────────────────────────────────────
def _invoke_with_retry(chain, payload: dict, desc: str = "LLM call", max_attempts: int = 3):
    """Invokes chain with automatic backoff if rate limited by Groq."""
    for attempt in range(1, max_attempts + 1):
        try:
            return chain.invoke(payload)
        except Exception as e:
            err_str = str(e).lower()
            if any(k in err_str for k in ["rate_limit", "413", "429", "tpm", "tokens per minute"]):
                wait_time = attempt * 7
                print(f"\n[Groq Rate Limit on {desc}]: Pausing {wait_time}s for token bucket recovery (attempt {attempt}/{max_attempts})...")
                time.sleep(wait_time)
            else:
                raise e
    return chain.invoke(payload)


def run_writer_critic_loop(topic: str, research: str):
    """Returns (report, feedback, rounds_used). Revises until score >= MIN_SCORE."""
    best = (None, "", -1.0)
    current_research = research
    rounds = 0

    for rounds in range(1, MAX_ROUNDS + 1):
        if rounds > 1:
            # Cool down between drafts to stay safely inside Groq's 8,000 TPM limit
            time.sleep(6)

        report = _invoke_with_retry(writer_chain, {"topic": topic, "research": current_research}, desc=f"Writer (Round {rounds})")
        
        # Brief pause between writer and critic
        time.sleep(3)
        
        feedback = _invoke_with_retry(critic_chain, {
            "report": report,
            "research": research[:CRITIC_RESEARCH_CHARS],
        }, desc=f"Critic (Round {rounds})")
        
        score = parse_score(feedback)
        rank = score if score is not None else 0.0
        if rank > best[2]:
            best = (report, feedback, rank)

        if score is not None and score >= MIN_SCORE:
            break
            
        current_research = (
            f"{research[:CRITIC_RESEARCH_CHARS]}\n\n"
            f"REVIEWER FEEDBACK ON PREVIOUS DRAFT (address every point):\n{feedback}"
        )

    return best[0], best[1], rounds


def run_research_pipeline(topic : str) -> dict:

    state = {}

    #search agent working
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    state["search_results"], urls = run_search_step(topic)

    print("\n search result ",state['search_results'])

    #step 2 - reader
    print("\n"+" ="*50)
    print("step 2 - Reader is scraping top resources ...")
    print("="*50)

    state['scraped_content'] = run_reader_step(urls)

    print("\nscraped content: \n", state['scraped_content'])

    #step 3 + 4 - writer and critic loop
    print("\n"+" ="*50)
    print("step 3/4 - Writer drafts, critic reviews (revises if score is low) ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"], state["feedback"], state["rounds"] = run_writer_critic_loop(
        topic, research_combined
    )

    print("\n Final Report\n",state['report'])
    print("\n critic report \n", state['feedback'])
    print(f"\n drafts written: {state['rounds']}")

    return state



if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)
