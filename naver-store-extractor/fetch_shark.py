"""shark ninja brand.naver.com 상품 데이터 캡처 (모든 응답 저장)"""
import asyncio
import random
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://brand.naver.com/sharkninja/products/12058921947"
PRODUCT_ID = sys.argv[2] if len(sys.argv) > 2 else "12058921947"
HEADLESS = "--headful" not in sys.argv
OUT_DIR = Path(f"output/{PRODUCT_ID}")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
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
                    print(f"[CAP] {url[:130]} ({len(body)})")
                except Exception:
                    pass

        page.on("response", on_resp)
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        print(f"GOTO {URL}")
        try:
            await page.goto(URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"goto warn: {e}")

        for _ in range(6):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1.2)
        await asyncio.sleep(3)

        html = await page.content()
        (OUT_DIR / "page.html").write_text(html, encoding="utf-8")
        print(f"URL now: {page.url}")

        for c in sorted(captured, key=lambda x: x["size"], reverse=True)[:12]:
            safe = str(c["size"])
            (OUT_DIR / f"cap_{safe}.json").write_bytes(c["body"])
            print(f"SAVE cap_{safe}.json <- {c['url'][:110]}")

        for c in captured:
            if f"/products/{PRODUCT_ID}" in c["url"] and "contents" not in c["url"]:
                (OUT_DIR / f"{PRODUCT_ID}_product.json").write_bytes(c["body"])
                print("SAVE product.json")
                break
        for c in captured:
            if "/contents/" in c["url"]:
                (OUT_DIR / f"{PRODUCT_ID}_raw.json").write_bytes(c["body"])
                print("SAVE raw.json")
                break

        try:
            print("TITLE:", await page.title())
        except Exception:
            pass
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
