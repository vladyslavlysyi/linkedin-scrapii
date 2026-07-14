import asyncio
import logging
import urllib.parse
import aiohttp
from typing import Dict, Any
from duckduckgo_search import AsyncDDGS

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

async def scrape_with_scraperapi(api_key: str, query: str):
    logger.info(f"Using native ScraperAPI Google Search mode")
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    payload = {
        'api_key': api_key,
        'url': url,
        'autoparse': 'true'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.scraperapi.com/', params=payload, timeout=60) as response:
            if response.status == 200:
                data = await response.json()
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
            else:
                text = await response.text()
                logger.error(f"ScraperAPI failed with status {response.status}: {text}")
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
    
    if not proxies_to_try:
        proxies_to_try.append(None) # try without proxy
        
    for proxy in proxies_to_try:
        # Check if this proxy is actually ScraperAPI
        if proxy and proxy.get('username') == 'scraperapi':
            api_key = proxy.get('password')
            if api_key:
                success = await scrape_with_scraperapi(api_key, query)
                if success:
                    return # exit successfully
                else:
                    logger.warning("ScraperAPI failed, trying next proxy...")
                    continue

        # Fallback to DuckDuckGo search
        proxy_url = proxy.get('server') if proxy else None
        
        if proxy_url and proxy and proxy.get('username'):
             ip_port = proxy_url.replace('http://', '').replace('https://', '')
             schema = 'https' if 'https' in proxy_url else 'http'
             user = proxy['username']
             pw = proxy['password']
             formatted_proxy = f"{schema}://{user}:{pw}@{ip_port}"
        else:
             formatted_proxy = proxy_url

        if formatted_proxy:
             logger.info(f"Trying Proxy on DuckDuckGo: {proxy_url}")
        else:
             logger.info("Trying without proxy on DuckDuckGo...")
        
        try:
            saved_count = 0
            async with AsyncDDGS(proxy=formatted_proxy) as ddgs:
                results = await ddgs.atext(query, max_results=50)
                logger.info(f"Found {len(results)} results from DDG API with this proxy.")
                
                for res in results:
                    person_data = await parse_ddgs_result(res)
                    if person_data:
                        await save_person(person_data)
                        saved_count += 1
                        
            logger.info(f"Successfully saved {saved_count} people in total.")
            return # Success! Exit the function
        except Exception as e:
            logger.error(f"Error with proxy {proxy_url}: {e}")
            
    logger.error("All proxies failed or were rate-limited.")
