# -*- coding: utf-8 -*-
"""블로그 전용 로그인 및 세션 저장 스크립트

블로그 글쓰기 권한 쿠키까지 완벽하게 저장합니다.
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESSION_PATH = Path("cookies/session.json")
SESSION_PATH.parent.mkdir(exist_ok=True)


async def main():
    print("\n========================================================")
    print("네이버 블로그 글쓰기 전용 로그인 창을 엽니다.")
    print("브라우저에서 로그인하시면 블로그 에디터로 자동 연결됩니다.")
    print("========================================================\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1300, "height": 950},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        page = await context.new_page()

        # 로그인 목적지를 블로그 글쓰기(GoBlogWrite)로 지정
        login_url = "https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2FGoBlogWrite.naver"
        await page.goto(login_url, wait_until="domcontentloaded")

        print("로그인 대기 중... (브라우저에서 로그인을 완료해 주세요)")

        # 블로그 글쓰기 페이지에 도달할 때까지 대기
        await page.wait_for_url(
            lambda u: "blog.naver.com" in u and "nidlogin" not in u,
            timeout=600000
        )
        await asyncio.sleep(3)

        print(f"\n[OK] 블로그 에디터 진입 확인: {page.url}")
        print("블로그 글쓰기 세션 쿠키를 영구 저장합니다...")
        await context.storage_state(path=str(SESSION_PATH))
        print(f"세션 저장 완료: {SESSION_PATH}")

        await page.screenshot(path="output/blog_login_success.png")
        print("확인 스크린샷 저장: output/blog_login_success.png")
        await asyncio.sleep(2)
        await browser.close()

    print("\n🎉 모든 준비가 끝났습니다! 이제 test_publish_private.py 를 실행하면 바로 글이 써집니다.")


if __name__ == "__main__":
    asyncio.run(main())

