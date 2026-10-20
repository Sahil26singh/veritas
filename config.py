import os
from dotenv import load_dotenv

load_dotenv()

# Groq model (must support tool calling). Override in .env with GROQ_MODEL=...
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Research depth (tuned to stay well within Groq free-tier 8,000 TPM limit)
MAX_URLS = 2            # how many pages the reader scrapes
SCRAPE_CHARS = 2000     # characters kept per scraped page
CRITIC_RESEARCH_CHARS = 3000   # how much research the critic sees to fact-check the report

# Critic loop
MIN_SCORE = 7           # accept report if critic score >= this
MAX_ROUNDS = 2          # max writer drafts (1 first draft + 1 revision)
