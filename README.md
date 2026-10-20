# Veritas (ResearchMind)

Most LLMs summarize from memory or skim quick search snippets—which often leads to hallucinations or surface-level answers. 

**Veritas** is a small multi-agent research pipeline that mimics how a human research team actually works: one person gathers real sources, another reads the full articles, a third drafts a detailed report, and a reviewer peer-reviews the draft to catch mistakes before anything gets finalized.

---

## What Actually Happens When You Run a Query

```
Your Topic 
    │
    ▼
[ 1. Search Agent ]  ──▶  Queries live web sources via Tavily API
    │
    ▼
[ 2. Reader Agent ]  ──▶  Pulls full page content in parallel (no snippet skimming)
    │
    ▼
[ 3. Writer Agent ]  ──▶  Synthesizes facts into a structured, cited report
    │
    ▼
[ 4. Critic Agent ]  ──▶  Audits claims, fact-checks against sources & scores (0-10)
    │                     
    ├─── Score < 7   ──▶  Sends feedback back to Writer for revisions
    └─── Score >= 7  ──▶  Final report ready with citations & markdown download
```

1. **Search Agent**: Takes your topic and calls Tavily's web search API to discover authoritative, live articles and documentation.
2. **Reader Agent**: Doesn't just rely on search snippets. It visits the top URLs concurrently using BeautifulSoup and pulls clean, dense body text.
3. **Writer Agent**: Reads through all the gathered research and writes a structured draft containing an Introduction, Key Findings, actionable takeaways, and source citations.
4. **Critic Agent**: Acts like a tough editor. It checks whether claims in the report are actually backed by the gathered sources, assigns an objective score out of 10, and points out weaknesses. If the draft scores below 7, it sends specific feedback back to the writer for an immediate rewrite.

---

## Getting Started

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/Sahil26singh/veritas.git
cd veritas

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

> **Free API keys**:
> - Groq API key: [console.groq.com](https://console.groq.com)
> - Tavily Search API key: [tavily.com](https://tavily.com)

---

## Running the Project

You can run Veritas either through a web interface or straight from your terminal:

### Option A: Clean Web Interface (Streamlit)
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. You get live step indicators, expandable raw sources, rendered markdown output, and a one-click `.md` download button.

### Option B: Terminal CLI
```bash
python pipeline.py
```
Prompts for a topic in your console and streams agent logs, drafted reports, and critic scores directly to stdout.

---

## Tuning the Pipeline (`config.py`)

All knobs are kept in [`config.py`](config.py) so you can tweak the pipeline without touching agent code:

| Setting | Default | Purpose |
| --- | --- | --- |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | LLM used across all agents |
| `MAX_URLS` | `2` | Number of webpages the Reader scrapes in parallel |
| `SCRAPE_CHARS` | `2000` | Max characters retained per page (keeps token limits safe) |
| `CRITIC_RESEARCH_CHARS`| `3000` | How much research context the Critic sees to verify claims |
| `MIN_SCORE` | `7` | Quality threshold needed to accept the report without rewriting |
| `MAX_ROUNDS` | `2` | Maximum drafts before finalizing the best version |

---

## Tech Behind It

- **Orchestration**: [LangChain](https://github.com/langchain-ai/langchain)
- **Fast LLM Inference**: [Groq Cloud](https://groq.com)
- **Live Search**: [Tavily Search API](https://tavily.com)
- **Scraping**: BeautifulSoup4 + Requests + LXML
- **Frontend**: Streamlit with custom CSS
