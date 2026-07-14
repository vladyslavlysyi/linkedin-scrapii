import asyncio
import logging
import random
import urllib.parse
from typing import Dict, Any

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from core.config import SEARCH_KEYWORDS, SEARCH_LOCATION, PROXIES_LIST
from core.database import save_person

logger = logging.getLogger(__name__)

async def human_delay():
    await asyncio.sleep(random.uniform(2, 5))

async def parse_ddglite_page(html: str) -> list[Dict[str, Any]]:
    results = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # DDG Lite puts results in tables
        tables = soup.find_all('table')
        if not tables:
            return results
            
        for tr in soup.find_all('tr'):
            td_title = tr.find('td', class_='result-snippet')
            if not td_title:
                continue
                
            a_tag = tr.find_previous_sibling('tr')
            if a_tag:
                a_tag = a_tag.find('a', class_='result-url')
                
            if not a_tag:
                continue
                
            link = a_tag.get('href', '')
            # Clean up DDG redirect if present
            if 'http' in link and 'uddg=' in link:
                try:
                    params = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                    if 'uddg' in params:
                        link = params['uddg'][0]
                except:
                    pass
                    
            if 'linkedin.com/in/' not in link:
                continue
                
            snippet = td_title.get_text(strip=True)
            full_title = a_tag.get_text(strip=True)
            
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
                
            link = link.split('?')[0]
            
            results.append({
                'name': name,
                'headline': headline,
                'profile_link': link,
                'snippet': snippet,
                'location': SEARCH_LOCATION
            })
    except Exception as e:
        logger.error(f"Error parsing DDG Lite page: {e}")
        
    return results

async def run_scraper():
    logger.info("Starting DuckDuckGo Lite Scraper (aiohttp)...")
    
    query_parts = [f'site:linkedin.com/in/', f'"{SEARCH_KEYWORDS}"']
    if SEARCH_LOCATION and SEARCH_LOCATION.lower() != "worldwide":
        query_parts.append(f'"{SEARCH_LOCATION}"')
    query = " ".join(query_parts)
    
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
    proxy_url = proxy.get('server') if proxy else None
    
    logger.info(f"Using Query: {query}")
    if proxy_url:
        logger.info(f"Using Proxy: {proxy_url}")
        
    saved_count = 0
    pages_to_scrape = 5
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Initial request
        data = {'q': query, 'kl': ''}
        url = "https://lite.duckduckgo.com/lite/"
        
        try:
            for page_index in range(pages_to_scrape):
                logger.info(f"Scraping DDG Lite Page {page_index+1}/{pages_to_scrape}...")
                
                async with session.post(url, data=data, proxy=proxy_url, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to fetch page, status: {resp.status}")
                        break
                        
                    html = await resp.text()
                    
                people = await parse_ddglite_page(html)
                logger.info(f"Found {len(people)} results on current page.")
                
                if not people:
                    if "duckduckgo.com" not in html.lower():
                         logger.warning("Possibly blocked by DDG (no results and layout missing).")
                    else:
                         logger.warning("No more results found.")
                    break
                    
                for person in people:
                    await save_person(person)
                    saved_count += 1
                    
                # Find Next button data
                soup = BeautifulSoup(html, 'html.parser')
                next_form = None
                for form in soup.find_all('form'):
                    if form.find('input', {'value': 'Next'}):
                        next_form = form
                        break
                        
                if not next_form:
                    logger.info("No 'Next' button found, reached the end.")
                    break
                    
                # Prepare data for next page
                data = {}
                for input_tag in next_form.find_all('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value', '')
                    if name:
                        data[name] = value
                        
                await human_delay()
                
        except Exception as e:
            logger.error(f"Error during DuckDuckGo Lite scraping: {e}")
            
    logger.info(f"Successfully saved {saved_count} people in total.")
