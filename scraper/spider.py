import asyncio
import logging
import random
from typing import Dict, Any

from playwright.async_api import async_playwright
from fake_useragent import UserAgent

from core.config import PROXIES_LIST, SEARCH_KEYWORDS, SEARCH_LOCATION
from core.database import save_job

logger = logging.getLogger(__name__)

async def human_delay():
    await asyncio.sleep(random.uniform(3, 9))

async def parse_job_card(page, card) -> Dict[str, Any]:
    try:
        # Evaluate all basic info in one go to prevent detached DOM node errors
        basic_info = await card.evaluate('''el => {
            const titleEl = el.querySelector('.base-search-card__title');
            const companyEl = el.querySelector('.base-search-card__subtitle');
            const locEl = el.querySelector('.job-search-card__location');
            const dateEl = el.querySelector('.job-search-card__listdate');
            const linkEl = el.querySelector('.base-card__full-link');
            
            let datePosted = "";
            if (dateEl) {
                datePosted = dateEl.getAttribute('datetime') || dateEl.innerText;
            }
            
            let link = linkEl ? linkEl.getAttribute('href') : "";
            if (link) {
                link = link.split('?')[0];
            }
            
            return {
                title: titleEl ? titleEl.innerText.trim() : "",
                company: companyEl ? companyEl.innerText.trim() : "",
                location: locEl ? locEl.innerText.trim() : "",
                date_posted: datePosted.trim(),
                job_link: link.trim()
            };
        }''')
        
        description = ""
        # Try to click and get description, but don't fail the whole parsing if it times out
        if basic_info['job_link']:
            try:
                await card.click(timeout=3000, force=True)
                await asyncio.sleep(random.uniform(1.5, 3))
                desc_elem = await page.query_selector('.show-more-less-html__markup')
                if desc_elem:
                    description = await desc_elem.inner_text()
            except Exception as e:
                logger.warning(f"Could not load description for '{basic_info['title']}': {e}")
        
        basic_info['description'] = description.strip()
        return basic_info
    except Exception as e:
        logger.error(f"Error parsing job card: {e}")
        return None

async def run_scraper():
    ua = UserAgent()
    pages_to_scrape = 4
    
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1920,1080',
        ]
        
        browser = await p.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        for page_index in range(pages_to_scrape):
            proxy = None
            if PROXIES_LIST:
                proxy = random.choice(PROXIES_LIST)
                
            context = await browser.new_context(
                user_agent=ua.random,
                viewport={'width': 1920, 'height': 1080},
                proxy=proxy
            )
            
            # Load playwright-stealth
            from playwright_stealth import stealth_async
            page = await context.new_page()
            await stealth_async(page)
            
            # Use &start= parameter for pagination (0, 25, 50, 75...)
            offset = page_index * 25
            url = f"https://www.linkedin.com/jobs/search/?keywords={SEARCH_KEYWORDS}&location={SEARCH_LOCATION}&start={offset}"
            
            proxy_url = proxy.get("server") if proxy else "None"
            logger.info(f"Page {page_index+1}/{pages_to_scrape}: Navigating to {url} using proxy: {proxy_url}")
            
            await page.goto(url)
            await human_delay()

            # Handle parsing on the loaded page
            cards = await page.query_selector_all('ul.jobs-search__results-list > li')
            num_cards = len(cards)
            logger.info(f"Found {num_cards} job cards on current view.")

            for i in range(num_cards):
                try:
                    # Re-fetch cards to avoid detached DOM node errors (React re-renders)
                    current_cards = await page.query_selector_all('ul.jobs-search__results-list > li')
                    if i >= len(current_cards):
                        break
                    card = current_cards[i]
                    
                    await card.scroll_into_view_if_needed()
                    job_data = await parse_job_card(page, card)
                    if job_data and job_data.get("job_link"):
                        await save_job(job_data)
                    await asyncio.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.error(f"Error processing card index {i}: {e}")
            
            # Close context to clear cookies, session, and disconnect proxy
            await context.close()
            
            logger.info("Taking a short break before the next page...")
            await human_delay()

        await browser.close()
