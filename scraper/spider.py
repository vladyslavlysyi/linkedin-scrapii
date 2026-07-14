import asyncio
import logging
from typing import Dict, Any
from duckduckgo_search import AsyncDDGS

from core.config import SEARCH_KEYWORDS, SEARCH_LOCATION
from core.database import save_person

logger = logging.getLogger(__name__)

async def parse_ddgs_result(result: dict) -> Dict[str, Any]:
    try:
        link = result.get('href', '')
        full_title = result.get('title', '')
        snippet = result.get('body', '')
        
        name = full_title
        headline = full_title
        
        if '-' in full_title:
            parts = full_title.split('-')
            name = parts[0].strip()
            headline = '-'.join(parts[1:]).replace(' | LinkedIn', '').replace(' - LinkedIn', '').strip()
        elif '|' in full_title:
            parts = full_title.split('|')
            name = parts[0].strip()
            headline = '|'.join(parts[1:]).replace('LinkedIn', '').strip()
            
        if link and 'linkedin.com/in/' in link:
            # Clean tracking params
            link = link.split('?')[0]
            
            return {
                'name': name,
                'headline': headline,
                'profile_link': link,
                'snippet': snippet,
                'location': SEARCH_LOCATION
            }
        return None
    except Exception as e:
        logger.error(f"Error parsing ddgs result: {e}")
        return None

async def run_scraper():
    logger.info("Starting DuckDuckGo API Scraper (No Playwright needed)...")
    
    query_parts = [f'site:linkedin.com/in/', f'"{SEARCH_KEYWORDS}"']
    if SEARCH_LOCATION and SEARCH_LOCATION.lower() != "worldwide":
        query_parts.append(f'"{SEARCH_LOCATION}"')
    query = " ".join(query_parts)
    
    logger.info(f"Using Query: {query}")
    
    try:
        saved_count = 0
        async with AsyncDDGS() as ddgs:
            # max_results limits how many profiles we get, DDGS handles pagination natively
            results = await ddgs.atext(query, max_results=50)
            
            logger.info(f"Found {len(results)} results from DDG API.")
            
            for res in results:
                person_data = await parse_ddgs_result(res)
                if person_data:
                    await save_person(person_data)
                    saved_count += 1
                    
        logger.info(f"Successfully saved {saved_count} people in total.")
    except Exception as e:
        logger.error(f"Error during DuckDuckGo API scraping: {e}")
