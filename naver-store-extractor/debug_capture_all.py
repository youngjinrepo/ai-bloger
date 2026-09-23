import asyncio
import random
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

if len(sys.argv) >= 3:
    URL = sys.argv[1]
    PRODUCT_ID = sys.argv[2]
else:
    URL = "https://brand.naver.com/babionkorea/products/455882425"
    PRODUCT_ID = "455882425"
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
            if "json" in ct:
                try:
                    body = await resp.body()
                    captured.append({"url": url, "size": len(body), "body": body})
                    print(f"[CAP] {url[:120]} (size={len(body)})")
                except Exception:
                    pass

        page.on("response", on_resp)

        print("naver.com 경유 중...")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2.0)

        print(f"페이지 로드: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(4.0)
        
        # Scroll down to trigger lazy loading APIs
        for _ in range(5):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1)

        print(f"\n=== 캡처된 API 응답 {len(captured)}개 ===")
        for i, c in enumerate(captured):
            if c['size'] > 1000:
                p_path = OUT_DIR / f"api_{i}.json"
                p_path.write_bytes(c["body"])
                print(f"[저장] {c['url'][:100]} -> api_{i}.json")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

