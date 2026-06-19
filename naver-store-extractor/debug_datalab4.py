"""datalab 쇼핑인사이트 - 식품(50000006) 선택 후 2분류 옵션 + 조회 결과 캡처"""
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"


async def main():
    result = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 1200},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()

        # API 응답 캡처
        captured = []
        async def on_resp(resp):
            if "getCategoryKeywordRank" in resp.url or "getCategoryClickTrend" in resp.url:
                try:
                    body = await resp.text()
                    captured.append({"url": resp.url, "body": body})
                except Exception:
                    pass
        page.on("response", on_resp)

        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        # 1차 분류: 식품 선택
        await page.click("text=패션의류")
        await asyncio.sleep(0.3)
        await page.click('a[data-cid="50000006"]')
        await asyncio.sleep(0.8)

        # 2차 분류 드롭다운 옵션 덤프
        # 두번째 select div 찾기
        selects = await page.query_selector_all("div.select")
        sub_options = []
        if len(selects) >= 2:
            second = selects[1]
            opts = await second.query_selector_all("a.option")
            for o in opts:
                cid = await o.get_attribute("data-cid")
                text = (await o.inner_text()).strip()
                sub_options.append({"cid": cid, "text": text})
        result["sub_options"] = sub_options

        await browser.close()

    Path("output/datalab_food_subcats.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("saved output/datalab_food_subcats.json")


if __name__ == "__main__":
    asyncio.run(main())
