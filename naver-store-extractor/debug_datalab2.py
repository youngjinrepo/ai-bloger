"""datalab 쇼핑인사이트 분야 드롭다운 구조 파악"""
import asyncio
import random
import sys
import json
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
            viewport={"width": 1280, "height": 1000},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        # select 요소 찾기
        selects = await page.query_selector_all("select")
        print(f"select 요소 개수: {len(selects)}")
        for i, sel in enumerate(selects):
            opts = await sel.query_selector_all("option")
            texts = []
            for o in opts:
                t = (await o.inner_text()).strip()
                v = await o.get_attribute("value")
                texts.append((v, t))
            print(f"\n[select #{i}]")
            for v, t in texts[:40]:
                print(f"   value={v!r} text={t!r}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
