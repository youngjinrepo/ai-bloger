"""datalab.naver.com 쇼핑인사이트 접근 가능 여부 1회 확인 (로그인 불필요 여부 체크)"""
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
            viewport={"width": 1280, "height": 1000},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()

        print(f"[fetch] {URL} 1회 로드...")
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        title = await page.title()
        print(f"  title: {title}")
        print(f"  url: {page.url}")

        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        shot_path = out_dir / "datalab_check.png"
        await page.screenshot(path=str(shot_path), full_page=False)
        print(f"  screenshot: {shot_path}")

        body_text = await page.inner_text("body")
        print(f"  '로그인' 포함: {'로그인' in body_text[:1500]}")
        print(f"  본문 앞 300자: {body_text[:300]!r}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
