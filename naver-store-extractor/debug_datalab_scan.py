"""식품 하위 카테고리 인기검색어 TOP 스캔 (cid 인자로 전달)"""
import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"


async def main(sub_cid: str, name: str):
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
        await page.click('a[data-cid="50000006"]')  # 식품
        await asyncio.sleep(0.8)

        await page.click(".select_btn >> nth=1")
        await asyncio.sleep(0.3)
        await page.click(f'a[data-cid="{sub_cid}"]')
        await asyncio.sleep(0.8)

        await page.click("text=조회하기")
        await asyncio.sleep(2)

        await page.screenshot(path=f"output/datalab_{name}.png", full_page=True)
        print(f"saved output/datalab_{name}.png")

        await browser.close()


if __name__ == "__main__":
    cid = sys.argv[1]
    name = sys.argv[2]
    asyncio.run(main(cid, name))
