import os
from dotenv import load_dotenv

load_dotenv()

# Groq models for separate rate-limit buckets
WRITER_MODEL = os.getenv("WRITER_MODEL", "openai/gpt-oss-120b")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "openai/gpt-oss-20b")

# Research depth and token budgets
MAX_URLS = int(os.getenv("MAX_URLS", "2"))            # how many pages the reader scrapes
SCRAPE_CHARS = int(os.getenv("SCRAPE_CHARS", "1500"))  # characters kept per scraped page
CRITIC_SOURCE_CHARS = int(os.getenv("CRITIC_SOURCE_CHARS", str(SCRAPE_CHARS)))  # matched to avoid false unsupported flags

# Quality threshold: revise at most once if critic score is below this
REVISE_BELOW = int(os.getenv("REVISE_BELOW", "6"))
