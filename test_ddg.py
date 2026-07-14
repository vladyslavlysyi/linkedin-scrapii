import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://lite.duckduckgo.com/lite/")
        await page.fill("input[name='q']", 'site:linkedin.com/in/ "Python Developer" "Ukraine"')
        await page.click("input[type='submit']")
        
        await page.wait_for_selector(".result-snippet")
        
        results = await page.query_selector_all("tr")
        for r in results:
            text = await r.inner_text()
            if "linkedin.com/in" in text:
                print("FOUND:", text)
                html = await r.inner_html()
                print("HTML:", html)
                
        await browser.close()

asyncio.run(main())
