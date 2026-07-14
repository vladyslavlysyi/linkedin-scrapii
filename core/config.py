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
    # Attempt to load from scraper/proxies.txt or fallback to .env PROXY_SERVER
    proxies = []
    proxy_file_path = os.path.join("scraper", "proxies.txt")
    if os.path.exists(proxy_file_path):
        with open(proxy_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                # Format: ip:port:username:password
                if "://" in line:
                    proxies.append({"server": line})
                else:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, pw = parts
                        proxies.append({
                            "server": f"http://{ip}:{port}",
                            "username": user,
                            "password": pw
                        })
                    elif len(parts) == 2:
                        ip, port = parts
                        proxies.append({
                            "server": f"http://{ip}:{port}"
                        })
    
    if not proxies and PROXY_SERVER:
        proxy = {"server": PROXY_SERVER}
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy["username"] = PROXY_USERNAME
            proxy["password"] = PROXY_PASSWORD
        proxies.append(proxy)
        
    return proxies

PROXIES_LIST = load_proxies()

# Scraping Settings
SEARCH_KEYWORDS = os.getenv("SEARCH_KEYWORDS", "Python Developer")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "Worldwide")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
