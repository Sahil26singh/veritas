# Veritas

Most LLMs summarize from memory or skim search snippets—which frequently leads to hallucinations or surface-level summaries.

**Veritas** is an optimized, rate-limit friendly research pipeline: it queries live web sources, reads complete articles, synthesizes a concise verified report with inline citations, and audits every factual claim against the sources.

---

## Architecture & Rate-Limit Minimization

```
Your Topic 
    │
    ▼
[ 1. Web Search ]      ──▶  Direct Tavily search query (0 LLM calls)
    │
    ▼
[ 2. Content Reader ]  ──▶  Scrapes full pages in parallel with backfill (0 LLM calls)
    │
    ▼
[ 3. Writer Chain ]    ──▶  Drafts concise report (<500 words) with citations [1], [2] (1 LLM call)
    │
    ▼
[ 4. Critic Chain ]    ──▶  Structured audit & claim verification (1 LLM call)
    │                     
    ├─── Score < 6     ──▶  Exactly one revision call addressing feedback (1 LLM call)
    └─── Score >= 6    ──▶  Accepted directly with citations & markdown export
```

### Strict 2–3 LLM Call Budget
- **Normal run**: Exactly **2 LLM calls** (Writer draft + Critic review).
- **Worst-case run**: Exactly **3 LLM calls** (1 draft + 1 review + 1 revision).
- **Zero LLM calls** in search or reader steps.
- **Dual Model Rate-Limit Isolation**: `WRITER_MODEL` and `CRITIC_MODEL` use separate Groq models to operate in independent rate-limit buckets.
- **Streamlit Caching**: All pipeline steps are wrapped in `@st.cache_data(ttl=3600)`, so repeat runs and reruns consume zero tokens and execute instantly.

---

## Getting Started

### 1. Virtual Environment Setup

```bash
git clone https://github.com/Sahil26singh/veritas.git
cd veritas

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the root directory (see `.env.example`):

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
WRITER_MODEL=openai/gpt-oss-120b
CRITIC_MODEL=openai/gpt-oss-20b
REVISE_BELOW=6
MAX_URLS=2
SCRAPE_CHARS=1500
```

> **Free API keys**:
> - Groq API key: [console.groq.com](https://console.groq.com)
> - Tavily Search API key: [tavily.com](https://tavily.com)

---

## Running Veritas

### Option A: Modern Web Interface (Streamlit)
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. Features live pipeline indicators, expandable source data, real interactive topic chips, structured critic feedback, and markdown export.

### Option B: Terminal CLI
```bash
python pipeline.py
```
Prompts for a topic in your console and streams execution results, formatted draft reports, and critic scores directly to stdout.

---

## Configuration (`config.py`)

All tuning options can be configured via environment variables or modified in [`config.py`](config.py):

| Setting | Default | Purpose |
| --- | --- | --- |
| `WRITER_MODEL` | `openai/gpt-oss-120b` | High-capability model for writing and synthesizing reports |
| `CRITIC_MODEL` | `openai/gpt-oss-20b` | Fast, separate model for structured claim verification |
| `REVISE_BELOW` | `6` | Minimum score (0–10) required to accept report without a revision |
| `MAX_URLS` | `2` | Number of webpages the reader scrapes concurrently |
| `SCRAPE_CHARS` | `1500` | Character limit per scraped page to prevent token bloat |

---

## Running Tests

Offline unit tests cover URL extraction, domain deduplication & selection, structured critic fallback, and the revise-at-most-once loop logic:

```bash
pytest
```
