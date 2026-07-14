import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "scraper_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "scraper_password")
DB_NAME = os.getenv("DB_NAME", "linkedin_jobs")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Proxy Configuration
PROXY_SERVER = os.getenv("PROXY_SERVER")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

def load_proxies():
    return []

PROXIES_LIST = load_proxies()

# Scraping Settings
SEARCH_KEYWORDS = os.getenv("SEARCH_KEYWORDS", "Python Developer")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "Worldwide")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
