import html
from pathlib import Path
import time
import streamlit as st

from pipeline import run_search_step, run_reader_step, run_writer_critic_loop


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Veritas · AI Research Assistant",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Load external CSS ────────────────────────────────────────────────────────
def load_css(file_name: str = "style.css"):
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()


# ── Streamlit caching wrappers (TTL 1 hour, hashable args) ───────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cached_search_step(topic: str):
    return run_search_step(topic)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_reader_step(urls: tuple):
    return run_reader_step(list(urls))


@st.cache_data(ttl=3600, show_spinner=False)
def cached_writer_critic_loop(topic: str, research: str, _on_progress=None):
    return run_writer_critic_loop(topic, research, on_progress=_on_progress)


# ── Helper: render a step card ────────────────────────────────────────────────
def step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done": ("✓ DONE", "status-done"),
    }
    label, cls = status_map.get(state, ("WAITING", "status-waiting"))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    desc_html = f"<div style='font-size:0.82rem;color:#64748b;margin-top:0.25rem;'>{desc}</div>" if desc else ""
    st.markdown(
        f"""
        <div class="step-card {card_cls}">
            <div class="step-header">
                <span class="step-num">{num}</span>
                <span class="step-title">{title}</span>
                <span class="step-status {cls}">{label}</span>
            </div>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Session state init ────────────────────────────────────────────────────────
for key, default in [
    ("results", {}),
    ("running", False),
    ("done", False),
    ("topic_input", ""),
    ("error_msg", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def set_topic(text: str):
    st.session_state.topic_input = text


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:6px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            Autonomous Research Pipeline
        </div>
        <h1>Veritas<span>.</span></h1>
        <p class="hero-sub">
            Gathers live web sources, reads complete articles, synthesizes verified reports, and audits factual claims.
        </p>
    </div>
    <div class="divider"></div>
    """,
    unsafe_allow_html=True,
)


# ── Layout: input left, pipeline right ───────────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    topic = st.text_input(
        "Research Topic",
        key="topic_input",
        label_visibility="visible",
    )
    btn_col1, btn_col2 = st.columns([1.25, 1])
    with btn_col1:
        run_btn = st.button("Run Pipeline", type="primary", icon=":material/bolt:", use_container_width=True)
    with btn_col2:
        fresh_btn = st.button("Re-run (Fresh)", key="rerun_fresh_btn", type="secondary", icon=":material/refresh:", use_container_width=True, help="Clears cache and forces a fresh query")

    # Example chips as interactive buttons
    st.markdown('<div class="try-label" style="margin-top:0.6rem;margin-bottom:0.4rem;">TRY A TOPIC →</div>', unsafe_allow_html=True)
    examples = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]
    chip_cols = st.columns(len(examples))
    for col, ex in zip(chip_cols, examples):
        with col:
            st.button(ex, key=f"chip_{ex}", on_click=set_topic, args=(ex,), use_container_width=True)

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline Status</div>', unsafe_allow_html=True)
    card_search = st.empty()
    card_reader = st.empty()
    card_writer = st.empty()
    card_critic = st.empty()

    def render_pipeline_cards(states: dict):
        with card_search:
            step_card("01", "Web Search", states.get("search", "waiting"), "Queries live web sources via Tavily")
        with card_reader:
            step_card("02", "Content Reader", states.get("reader", "waiting"), "Scrapes & extracts deep page content")
        with card_writer:
            step_card("03", "Report Writer", states.get("writer", "waiting"), "Drafts concise cited research report")
        with card_critic:
            step_card("04", "Critic Evaluation", states.get("critic", "waiting"), "Audits claims, fact-checks & scores")

    # Initial card render
    if st.session_state.done and st.session_state.results:
        init_state = "done"
    elif st.session_state.running:
        init_state = "running"
    else:
        init_state = "waiting"

    render_pipeline_cards({
        "search": init_state,
        "reader": init_state,
        "writer": init_state,
        "critic": init_state,
    })


# ── Run pipeline ─────────────────────────────────────────────────────────────
if fresh_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        cached_search_step.clear()
        cached_reader_step.clear()
        cached_writer_critic_loop.clear()
        st.session_state.results = {}
        st.session_state.error_msg = None
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()

if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.error_msg = None
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()

if st.session_state.running and not st.session_state.done:
    topic_val = st.session_state.topic_input
    try:
        # ── Step 1: Search ──
        render_pipeline_cards({"search": "running", "reader": "waiting", "writer": "waiting", "critic": "waiting"})
        with st.spinner("Discovering authoritative sources..."):
            search_text, urls = cached_search_step(topic_val)
            # Store partial result immediately
            st.session_state.results["search"] = search_text
            st.session_state.results["urls"] = urls

        # ── Step 2: Reader ──
        render_pipeline_cards({"search": "done", "reader": "running", "writer": "waiting", "critic": "waiting"})
        with st.spinner("Scraping and extracting page content in parallel..."):
            scraped_content = cached_reader_step(tuple(urls))
            # Store partial result immediately
            st.session_state.results["reader"] = scraped_content

        # ── Step 3 + 4: Writer & Critic ──
        def on_writer_critic_progress(stage: str):
            if stage == "writer":
                render_pipeline_cards({"search": "done", "reader": "done", "writer": "running", "critic": "waiting"})
            elif stage == "critic":
                render_pipeline_cards({"search": "done", "reader": "done", "writer": "done", "critic": "running"})
            elif stage == "revision":
                render_pipeline_cards({"search": "done", "reader": "done", "writer": "running", "critic": "done"})

        research_combined = (
            f"SEARCH RESULTS:\n{st.session_state.results['search']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{st.session_state.results['reader']}"
        )

        with st.spinner("Synthesizing research report & auditing claims..."):
            report, feedback, rounds = cached_writer_critic_loop(
                topic_val, research_combined, _on_progress=on_writer_critic_progress
            )
            # Store final results
            st.session_state.results["writer"] = report
            st.session_state.results["critic"] = feedback
            st.session_state.results["rounds"] = rounds

        render_pipeline_cards({"search": "done", "reader": "done", "writer": "done", "critic": "done"})

    except Exception as e:
        st.session_state.error_msg = str(e)
        st.error(f"Pipeline error: {e}")

    st.session_state.running = False
    st.session_state.done = True
    st.rerun()


# ── Results display ──────────────────────────────────────────────────────────
r = st.session_state.results

if st.session_state.error_msg:
    st.error(f"Pipeline encountered an issue: {st.session_state.error_msg}")

if r:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Research Results</div>', unsafe_allow_html=True)

    # Raw outputs in expanders
    if "search" in r and r["search"]:
        with st.expander("Search Output (Raw Sources)", icon=":material/search:", expanded=False):
            st.markdown(
                f'<div class="result-panel"><div class="result-panel-title">'
                f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:5px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
                f'Search Output & URLs</div>'
                f'<div class="result-content">{html.escape(r["search"])}</div></div>',
                unsafe_allow_html=True,
            )

    if "reader" in r and r["reader"]:
        with st.expander("Reader Output (Scraped Content)", icon=":material/travel_explore:", expanded=False):
            st.markdown(
                f'<div class="result-panel"><div class="result-panel-title">'
                f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:5px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>'
                f'Parallel Web Scraping</div>'
                f'<div class="result-content">{html.escape(r["reader"])}</div></div>',
                unsafe_allow_html=True,
            )

    # Final report container
    if "writer" in r and r["writer"]:
        with st.container(border=True):
            st.markdown(
                """
                <div class="panel-label orange">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:6px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                    Final Research Report
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(r["writer"])

        # Download button
        st.download_button(
            label="Download Report (.md)",
            data=r["writer"],
            file_name=f"veritas_report_{int(time.time())}.md",
            mime="text/markdown",
            icon=":material/download:",
            use_container_width=True,
        )

    # Critic feedback container
    if "critic" in r and r["critic"]:
        rounds_taken = r.get("rounds", 1)
        if rounds_taken > 1:
            critic_title = "Critic Evaluation & Score (Initial Draft — Revised in Final)"
            revision_alert = "> ℹ️ **Note:** This score and review evaluated the **first draft**. The final report above was revised once to incorporate these fixes; the critic was not re-run to conserve Groq rate limits."
        else:
            critic_title = "Critic Evaluation & Score (Accepted on First Draft)"
            revision_alert = ""

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="panel-label green">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    {critic_title}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if revision_alert:
                st.markdown(revision_alert)
            critic_data = r["critic"]
            if hasattr(critic_data, "to_markdown"):
                st.markdown(critic_data.to_markdown())
            elif isinstance(critic_data, dict):
                score_val = critic_data.get("score", "N/A")
                verdict_val = critic_data.get("verdict", "")
                unsupported = critic_data.get("unsupported_claims", [])
                fixes = critic_data.get("fixes", [])
                lines = [
                    f"**Score:** {score_val}/10",
                    f"**Verdict:** {verdict_val}",
                    "",
                    "**Unsupported Claims:**",
                ]
                if unsupported:
                    lines.extend([f"- {c}" for c in unsupported])
                else:
                    lines.append("- None identified. All claims appear grounded in sources.")
                lines.append("")
                lines.append("**Recommended Fixes:**")
                if fixes:
                    lines.extend([f"- {f}" for f in fixes])
                else:
                    lines.append("- None needed.")
                st.markdown("\n".join(lines))
            else:
                st.markdown(str(critic_data))


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="notice">
        Veritas · Powered by LangChain pipeline & Groq · Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)