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

async def parse_bing_result(card) -> Dict[str, Any]:
    try:
        # Evaluate to extract info from Bing result (li.b_algo)
        info = await card.evaluate('''el => {
            const linkEl = el.querySelector('h2 a');
            const snippetEl = el.querySelector('.b_caption p') || el.querySelector('.b_algoSlug') || el.innerText;
            
            let link = linkEl ? linkEl.getAttribute('href') : "";
            let fullTitle = linkEl ? linkEl.innerText : "";
            let snippet = snippetEl && typeof snippetEl !== "string" ? snippetEl.innerText : "";
            
            // Basic parsing of LinkedIn title (e.g. "John Doe - Software Engineer - Google | LinkedIn")
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
            # Clean tracking params from URL
            info['profile_link'] = info['profile_link'].split('?')[0]
            info['location'] = SEARCH_LOCATION # Assign search location since exact is hard from snippet
            return info
        return None
    except Exception as e:
        logger.error(f"Error parsing bing result: {e}")
        return None

async def run_scraper():
    ua = UserAgent()
    pages_to_scrape = 5 # Bing pages (10 results per page)
    
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080',
        ]
        
        browser = await p.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        # Build Bing Dork query
        # e.g., site:linkedin.com/in/ "Python Developer" "London"
        query = f'site:linkedin.com/in/ "{SEARCH_KEYWORDS}" "{SEARCH_LOCATION}"'
        encoded_query = urllib.parse.quote_plus(query)
        
        for page_index in range(pages_to_scrape):
            proxy = None
            if PROXIES_LIST:
                proxy = random.choice(PROXIES_LIST)
                
            context = await browser.new_context(
                user_agent=ua.random,
                viewport={'width': 1920, 'height': 1080},
                proxy=proxy
            )
            
            from playwright_stealth import stealth_async
            page = await context.new_page()
            await stealth_async(page)
            
            # Bing uses first=1, 11, 21 for pagination
            first = (page_index * 10) + 1
            url = f"https://www.bing.com/search?q={encoded_query}&first={first}"
            
            proxy_url = proxy.get("server") if proxy else "None"
            logger.info(f"Page {page_index+1}/{pages_to_scrape}: Navigating to Bing (Proxy: {proxy_url})")
            
            try:
                await page.goto(url, wait_until="domcontentloaded")
                await human_delay()
                
                # Check for captcha or blocks on Bing
                if "b_captcha" in await page.content():
                    logger.warning("Bing CAPTCHA detected. Skipping this page / trying new proxy next time.")
                    await context.close()
                    continue
                
                # Parse Bing results
                results = await page.query_selector_all('li.b_algo')
                logger.info(f"Found {len(results)} search results on current Bing page.")
                
                saved_count = 0
                for result in results:
                    person_data = await parse_bing_result(result)
                    if person_data:
                        await save_person(person_data)
                        saved_count += 1
                        
                logger.info(f"Successfully saved {saved_count} people from page {page_index+1}")
                
            except Exception as e:
                logger.error(f"Error on page {page_index+1}: {e}")
            
            await context.close()
            logger.info("Taking a break before the next Bing page...")
            await human_delay()

        await browser.close()
