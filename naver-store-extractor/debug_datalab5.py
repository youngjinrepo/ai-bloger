"""datalab 쇼핑인사이트 - 농산물/수산물 인기검색어 TOP 추출 (최근 1개월)"""
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"

# (대분류 cid, 소분류 cid, 이름)
TARGETS = [
    ("50000006", "50000160", "농산물"),
    ("50000006", "50000159", "수산물"),
    ("50000006", "50000026", "냉동/간편조리식품"),
]


async def extract_rank_list(page):
    items = []
    lis = await page.query_selector_all("div.section_keyword li, div.rank_top1000_box li, ul.rank_top1000 li")
    for li in lis:
        t = (await li.inner_text()).strip()
        if t:
            items.append(t)
    return items


async def main():
    results = {}
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

        for top_cid, sub_cid, name in TARGETS:
            # 1차 분류
            await page.click("li.active >> nth=5") if False else None
            # 1차 드롭다운 열기 (현재 선택된 버튼 클릭)
            await page.click(".select_btn >> nth=0")
            await asyncio.sleep(0.3)
            await page.click(f'a[data-cid="{top_cid}"]')
            await asyncio.sleep(0.6)

            # 2차 드롭다운 열기
            await page.click(".select_btn >> nth=1")
            await asyncio.sleep(0.3)
            await page.click(f'a[data-cid="{sub_cid}"]')
            await asyncio.sleep(0.6)

            # 조회하기 클릭
            await page.click("text=조회하기")
            await asyncio.sleep(1.5)

            items = await extract_rank_list(page)
            results[name] = items
            print(f"{name}: {len(items)}개 항목 추출")

            if not items:
                # fallback: 전체 텍스트에서 우측 패널 찾기
                html = await page.content()
                Path(f"output/datalab_debug_{name}.html").write_text(html, encoding="utf-8")

        await browser.close()

    Path("output/datalab_top_keywords.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("saved output/datalab_top_keywords.json")


if __name__ == "__main__":
    asyncio.run(main())
