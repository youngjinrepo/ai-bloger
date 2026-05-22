"""debug: 7515598524 product content capture"""
import asyncio
import random
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright

URL = "https://brand.naver.com/gokmuldogam/products/7515598524"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            storage_state=str(SESSION_PATH),
        )
        page = await ctx.new_page()
        content_body = None

        async def on_resp(resp):
            nonlocal content_body
            if "/contents/" in resp.url and "isResponsive" in resp.url:
                try:
                    body = await resp.body()
                    content_body = body
                    print(f"[CAP] {resp.url[:120]}", flush=True)
                    print(f"  Size: {len(body)} bytes", flush=True)
                except Exception as e:
                    print(f"  Error: {e}", flush=True)

        page.on("response", on_resp)
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(3)

        if content_body:
            out_path = Path("output/7515598524_raw.json")
            out_path.write_bytes(content_body)
            print(f"Saved: {out_path}")
            data = json.loads(content_body)
            render_html = data.get("renderContent", "")
            print(f"renderContent length: {len(render_html)}")
            urls = re.findall(r"https://shop-phinf\.pstatic\.net[^\"'<>\s\\]+", render_html)
            print(f"Image URLs found: {len(urls)}")
            for u in urls[:15]:
                print(f"  {u[:100]}")
        else:
            print("No content body captured - trying page HTML")
            html = await page.content()
            print(f"Page HTML length: {len(html)}")
            # Save HTML for inspection
            Path("output/7515598524_page.html").write_text(html, encoding="utf-8")
            print("Saved page HTML")

        # Get page title
        title = await page.title()
        print(f"Title: {title}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
