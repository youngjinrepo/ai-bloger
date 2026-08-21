"""헤드풀로 캡차를 사용자가 통과한 뒤, 그 세션 그대로 전부 수집.

- 캡차 통과 감지 → 세션(storage_state) 저장해서 이후 헤드리스 실행도 살림
- 상품/상세/공지 API 캡처
- 리뷰 전량 수집 (인기순 + 낮은점수순)

사용법:
  python fetch_after_captcha.py <URL> [PRODUCT_ID]
"""
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://smartstore.naver.com/bluebitestore/products/11065581834"
PRODUCT_ID = sys.argv[2] if len(sys.argv) > 2 else URL.rstrip("/").split("/products/")[-1].split("?")[0]
OUT_DIR = Path(f"output/{PRODUCT_ID}")
RANKING_PAGES = 9
LOW_PAGES = 7


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured, seen_req = [], {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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
                seen_req["url"] = req.url
                seen_req["body"] = req.post_data

        async def on_resp(resp):
            if "json" not in resp.headers.get("content-type", ""):
                return
            try:
                body = await resp.body()
            except Exception:
                return
            u = resp.url
            if PRODUCT_ID in u or "/contents/" in u or "notices" in u:
                captured.append({"url": u, "size": len(body), "body": body})

        page.on("request", on_req)
        page.on("response", on_resp)

        print("브라우저가 열립니다. 보안 확인(캡차)이 뜨면 직접 풀어주세요.")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(2)
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("goto warn:", str(e)[:80])

        print("상품 페이지 대기 중... 캡차 풀고 상품이 보이면 자동 진행됩니다.")
        ok = False
        for i in range(300):
            await asyncio.sleep(2)
            if any(f"/products/{PRODUCT_ID}" in c["url"] and c["size"] > 5000 for c in captured):
                ok = True
                break
            if i % 15 == 0 and i > 0:
                print(f"  ...대기 중 ({i*2}초)")
        if not ok:
            print("상품 API 미포착. 캡차를 통과하지 못했습니다.")
            await browser.close()
            return

        print("상품 감지 완료. 세션 저장 중...")
        await ctx.storage_state(path=str(SESSION_PATH))
        print(f"  세션 저장: {SESSION_PATH}")

        print("리뷰 영역까지 스크롤...")
        for _ in range(12):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1.0)
        await asyncio.sleep(3)

        for c in sorted(captured, key=lambda x: -x["size"]):
            if f"/products/{PRODUCT_ID}" in c["url"] and "contents" not in c["url"] and c["size"] > 5000:
                (OUT_DIR / f"{PRODUCT_ID}_product.json").write_bytes(c["body"])
                break
        for c in sorted(captured, key=lambda x: -x["size"]):
            if "/contents/" in c["url"] and c["size"] > 5000:
                (OUT_DIR / f"{PRODUCT_ID}_raw.json").write_bytes(c["body"])
                break
        print(f"캡처 API {len(captured)}건 저장 완료")

        if "body" not in seen_req:
            print("리뷰 요청 미포착 (리뷰 탭까지 스크롤되지 않음)")
            await browser.close()
            return

        base = json.loads(seen_req["body"])

        async def call(body):
            return await page.evaluate(
                """async ([u, b]) => {
                    const r = await fetch(u, {method:'POST',
                        headers:{'Content-Type':'application/json'},
                        body: JSON.stringify(b), credentials:'include'});
                    return r.status + '||' + await r.text();
                }""",
                [seen_req["url"], body],
            )

        for sort, pages, fname in [
            ("REVIEW_RANKING", RANKING_PAGES, "reviews_all.json"),
            ("REVIEW_SCORE_ASC", LOW_PAGES, "reviews_low.json"),
        ]:
            allr = []
            for pg in range(1, pages + 1):
                body = dict(base)
                body["page"] = pg
                body["reviewSearchSortType"] = sort
                st, _, txt = (await call(body)).partition("||")
                try:
                    items = json.loads(txt).get("contents", [])
                except Exception:
                    print(f"  {sort} p{pg} 실패 status={st}")
                    break
                if not items:
                    break
                allr.extend(items)
                print(f"  {sort} p{pg}: {len(items)}건 (누적 {len(allr)})")
                await asyncio.sleep(0.7)
            if allr:
                (OUT_DIR / fname).write_text(
                    json.dumps(allr, ensure_ascii=False, indent=1), encoding="utf-8"
                )
                print(f"저장: {OUT_DIR / fname} ({len(allr)}건)")

        await browser.close()
        print("\n완료.")


if __name__ == "__main__":
    asyncio.run(main())
