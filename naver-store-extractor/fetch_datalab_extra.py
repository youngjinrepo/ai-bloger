"""추가 카테고리 데이터랩 스캔"""
import asyncio
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

EXTRA_TARGETS = [
    ("50000006", "50000026", "가공식품"),
    ("50000006", "50000158", "건강식품"),
    ("50000006", "50001050", "젓갈장류"),
]


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
        await page.goto(
            "https://datalab.naver.com/shoppingInsight/sCategory.naver",
            wait_until="networkidle",
            timeout=40000,
        )
        await asyncio.sleep(1)

        for top_cid, sub_cid, name in EXTRA_TARGETS:
            try:
                await page.click(".select_btn >> nth=0")
                await asyncio.sleep(0.4)
                await page.click(f'a[data-cid="{top_cid}"]')
                await asyncio.sleep(0.7)
                await page.click(".select_btn >> nth=1")
                await asyncio.sleep(0.4)
                await page.click(f'a[data-cid="{sub_cid}"]')
                await asyncio.sleep(0.7)
                await page.click("text=조회하기")
                await asyncio.sleep(2.5)
                html = await page.content()
                Path(f"output/dl_{name}.html").write_text(html, encoding="utf-8")
                kws = re.findall(r"\d+</span>([^<\s][^<]*)", html)
                kws = [k.strip() for k in kws if k.strip()]
                print(f"\n=== {name} TOP {len(kws)} ===")
                for i, k in enumerate(kws[:30], 1):
                    print(f"  {i:2d}. {k}")
            except Exception as e:
                print(f"{name} 오류: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
