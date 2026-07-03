"""간장게장 brand.naver.com 상품 데이터 캡처"""
import asyncio
import random
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

URL = "https://brand.naver.com/koreasusan1/products/8772335977"
PRODUCT_ID = "8772335977"
OUT_DIR = Path(f"output/{PRODUCT_ID}")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = []

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

        async def on_resp(resp):
            url = resp.url
            ct = resp.headers.get("content-type", "")
            if "json" in ct and (PRODUCT_ID in url or "simple-products" in url or "products" in url):
                try:
                    body = await resp.body()
                    captured.append({"url": url, "size": len(body), "body": body})
                    print(f"[CAP] {url[:120]} ({len(body)} bytes)")
                except Exception:
                    pass

        page.on("response", on_resp)
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        print(f"로드: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(3)

        title = await page.title()
        print(f"페이지 제목: {title}")

        for c in sorted(captured, key=lambda x: x["size"], reverse=True):
            sz = c["size"]
            fname = OUT_DIR / f"cap_{sz}.json"
            fname.write_bytes(c["body"])
            print(f"\n=== 저장: {fname} ===")
            try:
                d = json.loads(c["body"])
                print(json.dumps(d, ensure_ascii=False, indent=2)[:3000])
            except Exception as e:
                print(f"파싱 오류: {e}")

        if not captured:
            html = await page.content()
            (OUT_DIR / "page.html").write_text(html, encoding="utf-8")
            print("캡처 없음 - HTML 저장됨")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
