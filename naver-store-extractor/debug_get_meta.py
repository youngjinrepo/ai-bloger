"""상품 메타데이터(이름/가격/평점)를 UTF-8 JSON으로 저장 (콘솔 인코딩 우회)"""
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from src.parser import parse_metadata, extract_product_id
from playwright.async_api import async_playwright


async def main(url: str):
    product_id = extract_product_id(url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx_kwargs = dict(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        if SESSION_PATH.exists():
            ctx_kwargs["storage_state"] = str(SESSION_PATH)
        ctx = await browser.new_context(**ctx_kwargs)
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        html = await page.content()
        meta = parse_metadata(html)

        out_dir = Path("output") / product_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "meta.json"
        out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"saved {out_path}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
