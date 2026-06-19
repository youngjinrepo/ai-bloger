"""brandconnect.naver.com 접근 가능 여부 1회 확인 (기존 smartstore 세션 재사용 시도)"""
import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright

URL = "https://brandconnect.naver.com/"


async def main():
    if not SESSION_PATH.exists():
        print(f"[ERROR] 세션 파일 없음: {SESSION_PATH}")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            storage_state=str(SESSION_PATH),
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()

        print(f"[fetch] {URL} 1회 로드...")
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(1)

        title = await page.title()
        print(f"  title: {title}")
        print(f"  url: {page.url}")

        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        shot_path = out_dir / "brandconnect_check.png"
        await page.screenshot(path=str(shot_path), full_page=False)
        print(f"  screenshot: {shot_path}")

        # 로그인 여부 추정: 로그인 버튼/문구 존재 여부
        body_text = await page.inner_text("body")
        is_login_prompt = "로그인" in body_text[:2000] and "로그아웃" not in body_text[:3000]
        print(f"  '로그인' 문구 포함(앞부분): {'로그인' in body_text[:2000]}")
        print(f"  '로그아웃' 문구 포함: {'로그아웃' in body_text}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
