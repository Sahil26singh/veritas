import streamlit as st
import time
import html
from pipeline import run_search_step, run_reader_step, run_writer_critic_loop

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS: Modern Light Theme ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@500;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #1e293b;
}

.stApp {
    background-color: #f8fafc;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(249, 115, 22, 0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 105%, rgba(59, 130, 246, 0.06) 0%, transparent 55%);
    color: #1e293b;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2.5rem 3rem 4rem; max-width: 1200px; }

/* ── Hero header ── */
.hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin: 0 auto;
    padding: 2.5rem 1rem 1.5rem;
    width: 100%;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin: 0 auto 1.2rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #c2410c;
    background: #ffedd5;
    border: 1px solid #fed7aa;
    padding: 0.35rem 1rem;
    border-radius: 9999px;
}
.hero h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.6rem, 5.5vw, 4.2rem) !important;
    font-weight: 800 !important;
    line-height: 1.05 !important;
    letter-spacing: -0.03em !important;
    color: #0f172a !important;
    text-align: center !important;
    margin: 0 auto 1rem !important;
    width: 100% !important;
}
.hero h1 span {
    color: #ea580c !important;
}
.hero-sub {
    font-size: 1.05rem !important;
    font-weight: 400 !important;
    color: #64748b !important;
    text-align: center !important;
    max-width: 620px !important;
    margin: 0 auto !important;
    line-height: 1.65 !important;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(234, 88, 12, 0.25), transparent);
    margin: 2rem auto;
    max-width: 900px;
    width: 100%;
}

/* ── Input card ── */
.input-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03);
}

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input {
    background: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    color: #0f172a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ea580c !important;
    box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15) !important;
}
.stTextInput > label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* ── Primary Button ── */
.stButton > button {
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    cursor: pointer !important;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s !important;
    box-shadow: 0 4px 16px rgba(234, 88, 12, 0.25) !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(234, 88, 12, 0.35) !important;
    opacity: 0.95 !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Pipeline Step Cards ── */
.step-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.9rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px -1px rgba(15, 23, 42, 0.04);
    transition: all 0.3s ease;
}
.step-card.active {
    border-color: #fb923c;
    background: #fff7ed;
    box-shadow: 0 4px 16px rgba(234, 88, 12, 0.1);
}
.step-card.done {
    border-color: #86efac;
    background: #f0fdf4;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.08);
}
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: #e2e8f0;
    transition: background 0.3s;
}
.step-card.active::before { background: #ea580c; }
.step-card.done::before   { background: #16a34a; }

.step-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
}
.step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #ea580c;
}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
}
.step-status {
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
}
.status-waiting  { color: #94a3b8; }
.status-running  { color: #ea580c; }
.status-done     { color: #16a34a; }

/* ── Result panels ── */
.result-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-top: 0.8rem;
    margin-bottom: 1.2rem;
}
.result-panel-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #ea580c;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}
.result-content {
    font-size: 0.92rem;
    line-height: 1.75;
    color: #334155;
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
}

/* ── Report & Feedback Panels ── */
.report-panel {
    background: #ffffff;
    border: 1.5px solid #fed7aa;
    border-radius: 16px;
    padding: 2.2rem 2.6rem;
    margin-top: 1rem;
    box-shadow: 0 4px 20px -2px rgba(234, 88, 12, 0.08);
}
.feedback-panel {
    background: #ffffff;
    border: 1.5px solid #bbf7d0;
    border-radius: 16px;
    padding: 2.2rem 2.6rem;
    margin-top: 1.5rem;
    box-shadow: 0 4px 20px -2px rgba(34, 197, 94, 0.08);
}
.panel-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    padding-bottom: 0.7rem;
}
.panel-label.orange {
    color: #c2410c;
    border-bottom: 1.5px solid #fed7aa;
}
.panel-label.green {
    color: #15803d;
    border-bottom: 1.5px solid #bbf7d0;
}

/* ── Section Headings ── */
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin: 1.5rem 0 1rem;
}

/* ── Spinner ── */
.stSpinner > div {
    color: #ea580c !important;
}

/* ── Expander ── */
details summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #475569 !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
}

/* ── Notice / Footer ── */
.notice {
    font-family: 'DM Mono', monospace;
    font-size: 0.74rem;
    color: #94a3b8;
    text-align: center;
    margin-top: 3.5rem;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)


# ── Helper: render a step card ────────────────────────────────────────────────
def step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done":    ("✓ DONE",   "status-done"),
    }
    label, cls = status_map.get(state, ("WAITING", "status-waiting"))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-header">
            <span class="step-num">{num}</span>
            <span class="step-title">{title}</span>
            <span class="step-status {cls}">{label}</span>
        </div>
        {"<div style='font-size:0.82rem;color:#64748b;margin-top:0.25rem;'>"+desc+"</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
for key in ("results", "running", "done", "topic_input"):
    if key not in st.session_state:
        st.session_state[key] = {} if key == "results" else ("" if key == "topic_input" else False)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;width:100%;margin:0 auto;">
    <div class="hero-eyebrow" style="margin:0 auto 1.2rem;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:6px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
        Multi-Agent AI System
    </div>
    <h1 style="text-align:center;margin:0 auto 1rem;width:100%;">Research<span>Mind</span></h1>
    <p class="hero-sub" style="text-align:center;margin:0 auto;max-width:620px;">
        Four specialized AI agents collaborate — searching, scraping, writing, and critiquing.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ── Layout: input left, pipeline right ───────────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    topic = st.text_input(
        "Research Topic",
        key="topic_input",
        label_visibility="visible",
    )
    run_btn = st.button("Run Research Pipeline", icon=":material/bolt:", use_container_width=True)

    # Example chips
    st.markdown("""
    <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;margin-bottom:1.5rem;">
        <span style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#94a3b8;letter-spacing:0.1em;font-weight:600;">TRY →</span>
    """, unsafe_allow_html=True)
    examples = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]
    for ex in examples:
        st.markdown(f"""
        <span style="
            background:#ffffff;
            border:1px solid #e2e8f0;
            border-radius:6px;
            padding:0.28rem 0.75rem;
            font-size:0.78rem;
            color:#475569;
            font-family:'DM Sans',sans-serif;
            box-shadow: 0 1px 3px rgba(15,23,42,0.03);
            cursor:default;
        ">{ex}</span>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)
    card_search = st.empty()
    card_reader = st.empty()
    card_writer = st.empty()
    card_critic = st.empty()

    def render_pipeline_cards(states: dict):
        with card_search:
            step_card("01", "Search Agent",  states.get("search", "waiting"), "Gathers recent authoritative web sources")
        with card_reader:
            step_card("02", "Reader Agent",  states.get("reader", "waiting"), "Scrapes & extracts deep page content")
        with card_writer:
            step_card("03", "Writer Chain",  states.get("writer", "waiting"), "Drafts the comprehensive research report")
        with card_critic:
            step_card("04", "Critic Chain",  states.get("critic", "waiting"), "Reviews, fact-checks & scores the report")

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


# ── Run pipeline: live step tracking, outputs update ONCE at end ─────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()

if st.session_state.running and not st.session_state.done:
    topic_val = st.session_state.topic_input
    results_temp = {}
    try:
        # ── Step 1: Search Agent ──
        render_pipeline_cards({"search": "running", "reader": "waiting", "writer": "waiting", "critic": "waiting"})
        with st.spinner("Search Agent is discovering authoritative sources..."):
            search_text, urls = run_search_step(topic_val)
            results_temp["search"] = search_text

        # ── Step 2: Reader Agent ──
        render_pipeline_cards({"search": "done", "reader": "running", "writer": "waiting", "critic": "waiting"})
        with st.spinner("Reader Agent is scraping page content in parallel..."):
            scraped_content = run_reader_step(urls)
            results_temp["reader"] = scraped_content

        # ── Step 3 + 4: Writer & Critic ──
        render_pipeline_cards({"search": "done", "reader": "done", "writer": "running", "critic": "waiting"})
        with st.spinner("Writer is drafting & Critic is reviewing report..."):
            research_combined = (
                f"SEARCH RESULTS:\n{results_temp['search']}\n\n"
                f"DETAILED SCRAPED CONTENT:\n{results_temp['reader']}"
            )
            report, feedback, rounds = run_writer_critic_loop(topic_val, research_combined)
            results_temp["writer"] = report
            results_temp["critic"] = feedback
            results_temp["rounds"] = rounds

        # ── Completed: All steps done ──
        render_pipeline_cards({"search": "done", "reader": "done", "writer": "done", "critic": "done"})

        # Update final research results state once at the end
        st.session_state.results = results_temp

    except Exception as e:
        st.error(f"Pipeline error: {e}")

    st.session_state.running = False
    st.session_state.done = True
    st.rerun()


# ── Results display (shown once completed at the end) ─────────────────────────
r = st.session_state.results

if r:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Research Results</div>', unsafe_allow_html=True)

    # Raw outputs in expanders
    if "search" in r and r["search"]:
        with st.expander("Search Agent Output (Raw Sources)", icon=":material/search:", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">'
                        f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:5px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
                        f'Search Output & URLs</div>'
                        f'<div class="result-content">{html.escape(r["search"])}</div></div>', unsafe_allow_html=True)

    if "reader" in r and r["reader"]:
        with st.expander("Reader Agent Output (Scraped Content)", icon=":material/travel_explore:", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">'
                        f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:5px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>'
                        f'Parallel Web Scraping</div>'
                        f'<div class="result-content">{html.escape(r["reader"])}</div></div>', unsafe_allow_html=True)

    # Final report
    if "writer" in r and r["writer"]:
        st.markdown("""
        <div class="report-panel">
            <div class="panel-label orange">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:6px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                Final Research Report
            </div>
        """, unsafe_allow_html=True)
        st.markdown(r["writer"])
        st.markdown("</div>", unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="Download Report (.md)",
            data=r["writer"],
            file_name=f"research_report_{int(time.time())}.md",
            mime="text/markdown",
            icon=":material/download:",
            use_container_width=True,
        )

    # Critic feedback
    if "critic" in r and r["critic"]:
        st.markdown("""
        <div class="feedback-panel">
            <div class="panel-label green">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                Critic Evaluation & Score
            </div>
        """, unsafe_allow_html=True)
        st.markdown(r["critic"])
        st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="notice">
    ResearchMind · Powered by LangChain multi-agent pipeline & Groq · Built with Streamlit
</div>
""", unsafe_allow_html=True)