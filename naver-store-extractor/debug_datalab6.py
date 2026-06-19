"""농산물 선택 후 결과 패널 HTML 구조 확인"""
import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 1400},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        await page.click(".select_btn >> nth=0")
        await asyncio.sleep(0.3)
        await page.click('a[data-cid="50000006"]')
        await asyncio.sleep(0.6)

        await page.click(".select_btn >> nth=1")
        await asyncio.sleep(0.3)
        await page.click('a[data-cid="50000160"]')
        await asyncio.sleep(0.6)

        await page.click("text=조회하기")
        await asyncio.sleep(2)

        html = await page.content()
        Path("output/datalab_result.html").write_text(html, encoding="utf-8")
        print("saved output/datalab_result.html, length=", len(html))

        await page.screenshot(path="output/datalab_result.png", full_page=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
