"""brand.naver.com renderContent에서 이미지 URL 추출 디버그"""
import asyncio
import random
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright

URL = "https://brand.naver.com/drblank/products/4960823242"


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

        async def on_resp(resp):
            if "/contents/" in resp.url and "isResponsive" in resp.url:
                try:
                    body = await resp.body()
                    print(f"[CAP] {resp.url[:120]}")
                    print(f"  크기: {len(body)} bytes")

                    # raw body 저장
                    Path("output/brand_debug_raw.json").write_bytes(body)
                    print("  → output/brand_debug_raw.json 저장")

                    data = json.loads(body)
                    render_html = data.get("renderContent", "")
                    print(f"  renderContent 길이: {len(render_html)}")

                    # 원본 fetcher 패턴
                    pattern1 = r"https://shop-phinf\.pstatic\.net[^\"'<>\s\\]+"
                    urls1 = re.findall(pattern1, render_html)
                    print(f"  shop-phinf (fetcher 패턴): {len(urls1)}개")
                    for u in urls1[:5]:
                        print(f"    {u[:100]}")

                    # 넓은 패턴
                    pattern2 = r"https?://[^\s\"'<>]+"
                    urls2 = re.findall(pattern2, render_html)
                    img_urls = [u for u in urls2 if any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])]
                    print(f"  이미지 URLs (넓은패턴): {len(img_urls)}개")
                    for u in img_urls[:10]:
                        print(f"    {u[:100]}")

                    # renderContent 앞 300자
                    print(f"\n  renderContent 앞 300자:\n  {render_html[:300]}")

                except Exception as e:
                    import traceback
                    print(f"  오류: {e}")
                    traceback.print_exc()

        page.on("response", on_resp)
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
