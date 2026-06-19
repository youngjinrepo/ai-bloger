"""datalab 쇼핑인사이트 - 분야 드롭다운 DOM 구조 덤프 + 클릭 시도"""
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
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        # 패션의류 텍스트가 들어있는 클릭 가능 요소 찾기
        el = await page.query_selector("text=패션의류")
        if el:
            html = await el.evaluate("e => e.outerHTML")
            print("=== 패션의류 요소 ===")
            print(html[:500])
            print("\n=== 부모 ===")
            parent_html = await el.evaluate("e => e.parentElement.outerHTML")
            print(parent_html[:1000])

            # 클릭해서 옵션 목록 나오는지 확인
            await el.click()
            await asyncio.sleep(0.5)
            await page.screenshot(path="output/datalab_dropdown.png")
            print("\nscreenshot saved: output/datalab_dropdown.png")

            # ul/li 옵션 찾기
            items = await page.query_selector_all("li")
            print(f"\nli 요소 개수: {len(items)}")
            for it in items[:60]:
                t = (await it.inner_text()).strip()
                if t:
                    cls = await it.get_attribute("class")
                    print(f"  [{cls}] {t!r}")
        else:
            print("패션의류 요소 못 찾음")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
