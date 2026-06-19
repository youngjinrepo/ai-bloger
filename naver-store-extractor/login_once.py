"""
최초 1회만 실행: 네이버 로그인 후 세션 저장.
저장된 세션은 이후 자동으로 재사용됨.
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

SESSION_PATH = Path("cookies/session.json")


async def main():
    SESSION_PATH.parent.mkdir(exist_ok=True)

    print("브라우저가 열립니다. 네이버에 로그인하세요.")
    print("로그인이 완료되면 자동으로 세션이 저장됩니다.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        page = await context.new_page()
        await page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")

        print("로그인 대기 중...")

        # 로그인 완료 감지: login URL에서 벗어나면 완료
        await page.wait_for_url(
            lambda url: "nidlogin" not in url and "naver.com" in url,
            timeout=600000,
        )

        print("로그인 감지됨. 세션 저장 중...")
        await context.storage_state(path=str(SESSION_PATH))
        await browser.close()

    print(f"\n[OK] 세션 저장 완료: {SESSION_PATH}")
    print("이제 python test_fetch.py 로 테스트하세요.")


if __name__ == "__main__":
    asyncio.run(main())
