"""데이터랩 쇼핑인사이트 API 응답 직접 캡처 — 식품 카테고리 인기검색어"""
import asyncio
import json
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS
from playwright.async_api import async_playwright

URL = "https://datalab.naver.com/shoppingInsight/sCategory.naver"

TARGETS = [
    ("50000006", "50000160", "농산물"),
    ("50000006", "50000159", "수산물"),
    ("50000006", "50000026", "냉동간편"),
    ("50000006", "50000161", "축산물"),
    ("50000006", "50001050", "젓갈장류"),
]


async def main():
    all_results = {}

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

        captured_apis = []

        async def on_resp(resp):
            url = resp.url
            ct = resp.headers.get("content-type", "")
            if "json" in ct and ("rank" in url or "keyword" in url or "shopping" in url.lower()):
                try:
                    body = await resp.body()
                    captured_apis.append({"url": url, "body": body})
                except Exception:
                    pass

        page.on("response", on_resp)

        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        for top_cid, sub_cid, name in TARGETS:
            captured_apis.clear()

            # 1차 드롭다운
            await page.click(".select_btn >> nth=0")
            await asyncio.sleep(0.4)
            await page.click(f'a[data-cid="{top_cid}"]')
            await asyncio.sleep(0.7)

            # 2차 드롭다운
            await page.click(".select_btn >> nth=1")
            await asyncio.sleep(0.4)
            await page.click(f'a[data-cid="{sub_cid}"]')
            await asyncio.sleep(0.7)

            # 조회
            await page.click("text=조회하기")
            await asyncio.sleep(2.5)

            # 스크린샷
            safe_name = name.replace("/", "_")
            await page.screenshot(path=f"output/dl_{safe_name}.png", full_page=False)

            # HTML에서 키워드 추출 시도
            html = await page.content()
            Path(f"output/dl_{safe_name}.html").write_text(html, encoding="utf-8")

            # API 응답 확인
            print(f"\n[{name}] 캡처된 API: {len(captured_apis)}개")
            for api in captured_apis:
                print(f"  {api['url'][:100]}")
                try:
                    d = json.loads(api["body"])
                    print(f"  내용: {json.dumps(d, ensure_ascii=False)[:300]}")
                    all_results[name] = d
                except Exception:
                    pass

            # HTML에서 직접 키워드 파싱 시도
            import re
            # 다양한 패턴 시도
            kw_patterns = [
                r'rank_top1000[^"]*"[^>]*>.*?<span[^>]*>(.+?)</span>',
                r'"keyword"\s*:\s*"([^"]+)"',
                r'class="item_title"[^>]*>([^<]+)<',
                r'<em class="rank_num">\d+</em>\s*<span[^>]*>([^<]+)</span>',
            ]
            found_kws = []
            for pat in kw_patterns:
                matches = re.findall(pat, html)
                if matches:
                    found_kws.extend(matches[:20])
                    break

            if found_kws:
                print(f"  HTML 파싱 키워드 {len(found_kws)}개: {found_kws[:10]}")
                all_results[name] = found_kws
            else:
                print(f"  키워드 추출 실패 — HTML 저장됨")

        await browser.close()

    out = Path("output/datalab_scan_result.json")
    out.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과 저장: {out}")


if __name__ == "__main__":
    asyncio.run(main())
