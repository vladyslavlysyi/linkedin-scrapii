import asyncio
import logging
from core.database import init_db
from scraper.spider import run_scraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Starting LinkedIn Scraper...")
    await run_scraper()
    
    logger.info("Scraping completed.")

if __name__ == "__main__":
    asyncio.run(main())
