import asyncio
import logging
import random
import urllib.parse
from typing import Dict, Any

from playwright.async_api import async_playwright
from fake_useragent import UserAgent

from core.config import PROXIES_LIST, SEARCH_KEYWORDS, SEARCH_LOCATION
from core.database import save_person

logger = logging.getLogger(__name__)

async def human_delay():
    await asyncio.sleep(random.uniform(3, 8))

async def parse_ddg_result(card) -> Dict[str, Any]:
    try:
        info = await card.evaluate('''el => {
            const linkEl = el.querySelector('.result__url');
            const titleEl = el.querySelector('.result__title');
            const snippetEl = el.querySelector('.result__snippet');
            
            let link = linkEl ? linkEl.getAttribute('href') : "";
            // DDG sometimes prepends their own redirect URL, extract the real one
            if (link.includes('?q=')) {
                try {
                    const urlParams = new URLSearchParams(link.split('?')[1]);
                    const realUrl = urlParams.get('q');
                    if (realUrl) link = realUrl;
                } catch(e) {}
            }
            
            let fullTitle = titleEl ? titleEl.innerText : "";
            let snippet = snippetEl ? snippetEl.innerText : "";
            
            // Basic parsing of LinkedIn title
            let name = fullTitle;
            let headline = fullTitle;
            
            if (fullTitle.includes('-')) {
                const parts = fullTitle.split('-');
                name = parts[0].trim();
                headline = parts.slice(1).join('-').replace(/\| LinkedIn/i, '').trim();
            } else if (fullTitle.includes('|')) {
                const parts = fullTitle.split('|');
                name = parts[0].trim();
                headline = parts.slice(1).join('|').replace(/LinkedIn/i, '').trim();
            }
            
            return {
                name: name,
                headline: headline,
                profile_link: link,
                snippet: snippet
            };
        }''')
        
        # We only want LinkedIn profiles
        if info['profile_link'] and 'linkedin.com/in/' in info['profile_link']:
            info['profile_link'] = info['profile_link'].split('?')[0]
            info['location'] = SEARCH_LOCATION
            return info
        return None
    except Exception as e:
        logger.error(f"Error parsing ddg result: {e}")
        return None

async def run_scraper():
    ua = UserAgent()
    pages_to_scrape = 5
    
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080',
        ]
        
        browser = await p.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        query = f'site:linkedin.com/in/ "{SEARCH_KEYWORDS}" "{SEARCH_LOCATION}"'
        encoded_query = urllib.parse.quote_plus(query)
        
        proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
        
        context = await browser.new_context(
            user_agent=ua.random,
            viewport={'width': 1920, 'height': 1080},
            proxy=proxy
        )
        
        from playwright_stealth import stealth_async
        page = await context.new_page()
        await stealth_async(page)
        
        # Start at the first page
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        proxy_url = proxy.get("server") if proxy else "None"
        logger.info(f"Navigating to DuckDuckGo HTML (Proxy: {proxy_url})")
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await human_delay()
            
            for page_index in range(pages_to_scrape):
                logger.info(f"Scraping DDG Page {page_index+1}/{pages_to_scrape}...")
                
                # Parse results
                results = await page.query_selector_all('.result')
                logger.info(f"Found {len(results)} search results on current DDG page.")
                
                if len(results) == 0:
                    logger.warning("No results found or blocked. Trying to take a screenshot for debugging (if possible) and stopping.")
                    break
                
                saved_count = 0
                for result in results:
                    person_data = await parse_ddg_result(result)
                    if person_data:
                        await save_person(person_data)
                        saved_count += 1
                        
                logger.info(f"Successfully saved {saved_count} people from page {page_index+1}")
                
                if page_index < pages_to_scrape - 1:
                    # Click Next button
                    next_button = await page.query_selector("input[value='Next']")
                    if not next_button:
                        logger.info("No 'Next' button found. Reached end of results.")
                        break
                        
                    logger.info("Clicking 'Next' button...")
                    await asyncio.gather(
                        page.wait_for_load_state("domcontentloaded"),
                        next_button.click()
                    )
                    await human_delay()
                    
        except Exception as e:
            logger.error(f"Error during DuckDuckGo scraping: {e}")
            
        await context.close()
        await browser.close()
