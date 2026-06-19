"""네이버 쇼핑 검색 결과 스크린샷 (키워드 인자로 전달)"""
import asyncio
import random
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright


async def main(keyword: str, name: str):
    encoded = urllib.parse.quote(keyword)
    url = f"https://search.shopping.naver.com/search/all?query={encoded}&sort=rel"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx_kwargs = dict(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 2200},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        if SESSION_PATH.exists():
            ctx_kwargs["storage_state"] = str(SESSION_PATH)
        ctx = await browser.new_context(**ctx_kwargs)
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1.5)

        await page.screenshot(path=f"output/shopping_{name}.png", full_page=True)
        print(f"saved output/shopping_{name}.png")

        await browser.close()


if __name__ == "__main__":
    keyword = sys.argv[1]
    name = sys.argv[2]
    asyncio.run(main(keyword, name))
