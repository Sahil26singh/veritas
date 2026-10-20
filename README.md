# ResearchMind - Multi-Agent Research System

Search agent -> Reader (parallel scraping) -> Writer <-> Critic loop.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY (console.groq.com) and TAVILY_API_KEY (tavily.com)
```

## Run
```bash
streamlit run app.py     # web UI
python pipeline.py       # CLI
```

## Tuning (config.py)
- `GROQ_MODEL` - model name (must support tool calling)
- `MAX_URLS`, `SCRAPE_CHARS` - how many pages / how much text per page
- `MIN_SCORE`, `MAX_ROUNDS` - critic acceptance score and max drafts
