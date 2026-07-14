import asyncio
import logging
import urllib.parse
import aiohttp
from typing import Dict, Any

from core.config import SEARCH_KEYWORDS, SEARCH_LOCATION, PROXIES_LIST
from core.database import save_person
import random

logger = logging.getLogger(__name__)

async def parse_google_result(res: dict) -> Dict[str, Any]:
    try:
        link = res.get('link', '')
        title = res.get('title', '')
        snippet = res.get('snippet', '')
        
        name = title
        headline = title
        
        if '-' in title:
            parts = title.split('-')
            name = parts[0].strip()
            headline = '-'.join(parts[1:]).replace(' | LinkedIn', '').replace(' - LinkedIn', '').strip()
        elif '|' in title:
            parts = title.split('|')
            name = parts[0].strip()
            headline = '|'.join(parts[1:]).replace('LinkedIn', '').strip()
            
        if link and 'linkedin.com/in/' in link:
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
        logger.error(f"Error parsing google result: {e}")
        return None

import requests

async def scrape_with_scraperapi(api_key: str, query: str):
    logger.info(f"Using native ScraperAPI Google Search mode")
    url = f"https://www.google.com/search?q={query}"
    
    payload = {
        'api_key': api_key,
        'url': url,
        'autoparse': 'true',
        'premium': 'true'
    }
    
    for attempt in range(3):
        try:
            # run requests.get in a separate thread so it doesn't block the async loop
            response = await asyncio.to_thread(
                requests.get, 
                'https://api.scraperapi.com/', 
                params=payload, 
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('organic_results', [])
                logger.info(f"ScraperAPI returned {len(results)} organic results")
                saved_count = 0
                for res in results:
                    person = await parse_google_result(res)
                    if person:
                        await save_person(person)
                        saved_count += 1
                logger.info(f"Successfully saved {saved_count} people from Google.")
                return True
            elif response.status_code == 500:
                logger.warning(f"ScraperAPI returned 500 (attempt {attempt+1}/3), retrying...")
                await asyncio.sleep(2)
            else:
                logger.error(f"ScraperAPI failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"ScraperAPI request error on attempt {attempt+1}: {e}")
            await asyncio.sleep(2)
    
    logger.error("ScraperAPI failed after 3 attempts.")
    return False

async def run_scraper():
    logger.info("Starting Scraper...")
    
    query_parts = [f'site:linkedin.com/in/', f'"{SEARCH_KEYWORDS}"']
    if SEARCH_LOCATION and SEARCH_LOCATION.lower() != "worldwide":
        query_parts.append(f'"{SEARCH_LOCATION}"')
    query = " ".join(query_parts)
    
    logger.info(f"Using Query: {query}")
    
    # Shuffle proxies to try random ones first
    proxies_to_try = PROXIES_LIST.copy()
    random.shuffle(proxies_to_try)
    
    for proxy in proxies_to_try:
        # Check if this proxy is actually ScraperAPI
        is_scraper_api = False
        api_key = None
        
        if proxy:
            server = proxy.get('server', '')
            if 'scraperapi' in server:
                is_scraper_api = True
                # Extract password from http://username:password@...
                if '@' in server:
                    auth_part = server.split('@')[0]
                    if ':' in auth_part:
                        api_key = auth_part.split(':')[-1]
            elif proxy.get('username') == 'scraperapi':
                is_scraper_api = True
                api_key = proxy.get('password')
                
        if is_scraper_api and api_key:
            success = await scrape_with_scraperapi(api_key, query)
            if success:
                return # exit successfully
            else:
                logger.warning("ScraperAPI failed, trying next proxy...")
                continue

    logger.error("No valid ScraperAPI key found or all failed.")
