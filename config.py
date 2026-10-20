import os
from dotenv import load_dotenv

load_dotenv()

# Groq model (must support tool calling). Override in .env with GROQ_MODEL=...
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Research depth
MAX_URLS = 3            # how many pages the reader scrapes
SCRAPE_CHARS = 4000     # characters kept per scraped page (keeps Groq free-tier token limits happy)

# Critic loop
MIN_SCORE = 7           # accept report if critic score >= this
MAX_ROUNDS = 2          # max writer drafts (1 first draft + 1 revision)
CRITIC_RESEARCH_CHARS = 6000   # how much research the critic sees to fact-check the report
