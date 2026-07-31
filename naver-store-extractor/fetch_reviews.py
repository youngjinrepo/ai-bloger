"""리뷰 API(query-pages) 요청 본문을 가로채 페이지별로 재요청해 리뷰 원문 수집"""
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://brand.naver.com/sharkninja/products/12058921947"
PRODUCT_ID = sys.argv[2] if len(sys.argv) > 2 else "12058921947"
PAGES = int(sys.argv[3]) if len(sys.argv) > 3 else 8
OUT_DIR = Path(f"output/{PRODUCT_ID}")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen_req = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            storage_state=str(SESSION_PATH),
        )
        await ctx.add_init_script(STEALTH_SCRIPT)
        page = await ctx.new_page()

        def on_req(req):
            if "reviews/query-pages" in req.url and req.method == "POST":
                try:
                    seen_req["url"] = req.url
                    seen_req["body"] = req.post_data
                except Exception:
                    pass

        page.on("request", on_req)
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        await page.goto(URL, wait_until="networkidle", timeout=60000)
        for _ in range(6):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1.0)
        await asyncio.sleep(3)

        if "body" not in seen_req:
            print("no review request captured")
            await browser.close()
            return

        print("captured body:", seen_req["body"][:400])
        base = json.loads(seen_req["body"])

        all_reviews = []
        for pg in range(1, PAGES + 1):
            body = dict(base)
            body["page"] = pg
            res = await page.evaluate(
                """async ([url, body]) => {
                    const r = await fetch(url, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(body),
                        credentials: 'include',
                    });
                    return await r.text();
                }""",
                [seen_req["url"], body],
            )
            try:
                d = json.loads(res)
                items = d.get("contents", [])
                all_reviews.extend(items)
                print(f"page {pg}: {len(items)} reviews (total {len(all_reviews)})")
                if not items:
                    break
            except Exception as e:
                print(f"page {pg} parse fail: {e} / {res[:200]}")
                break
            await asyncio.sleep(0.8)

        out = OUT_DIR / "reviews_all.json"
        out.write_text(json.dumps(all_reviews, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"saved {out} ({len(all_reviews)})")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
