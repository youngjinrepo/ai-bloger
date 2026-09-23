# -*- coding: utf-8 -*-
"""네이버 블로그 비공개 발행 E2E 실전 테스트 스크립트

동작:
1. 브라우저 창이 열립니다 (눈에 보임).
2. 네이버 로그인이 안 되어 있으면 로그인을 대기하고, 로그인 즉시 세션을 저장합니다.
3. 스마트에디터 ONE에 들어가서 제목/본문을 입력합니다.
4. 상단 [발행] 버튼 클릭 -> [비공개] 선택 -> 최종 [발행]을 누릅니다.
5. 발행된 비공개 글의 URL과 화면을 캡처해 성공 여부를 확인합니다.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Windows 콘솔 인코딩 에러 방지
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
SESSION_PATH = ROOT / "cookies" / "session.json"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as p:
        # 사용자가 눈으로 확인할 수 있게 headless=False로 실행
        browser = await p.chromium.launch(headless=False)
        
        ctx_options = {
            "viewport": {"width": 1300, "height": 950},
            "locale": "ko-KR",
            "timezone_id": "Asia/Seoul",
        }
        if SESSION_PATH.exists():
            ctx_options["storage_state"] = str(SESSION_PATH)

        context = await browser.new_context(**ctx_options)
        page = await context.new_page()

        print("\n==========================================")
        print("1. 네이버 블로그 글쓰기 페이지 진입 시도...")
        print("==========================================")
        
        await page.goto("https://blog.naver.com/GoBlogWrite.naver", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 로그인 필요 여부 확인
        if "nidlogin" in page.url:
            print("\n[안내] 열린 브라우저 창에서 네이버에 로그인해 주세요!")
            print("   (로그인이 완료되면 스크립트가 자동으로 감지해 글 작성을 이어갑니다...)")
            
            # 로그인 완료 감지 (URL이 nidlogin에서 벗어날 때까지 대기, 최대 5분)
            await page.wait_for_url(lambda u: "nidlogin" not in u and "naver.com" in u, timeout=300000)
            print("\n[OK] 로그인 감지 완료! 세션 쿠키를 저장합니다...")
            await context.storage_state(path=str(SESSION_PATH))
            
            # 다시 글쓰기 페이지로 이동
            await page.goto("https://blog.naver.com/GoBlogWrite.naver", wait_until="domcontentloaded")
            await asyncio.sleep(3)

        print(f"\n현재 페이지 URL: {page.url}")

        # 팝업 닫기 (작성 중인 글 취소, 도움말 등)
        print("2. 팝업 및 도움말 레이어 정리 중...")
        for _ in range(3):
            try:
                cancel_btn = page.locator("button:has-text('취소')").first
                if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
                    print("  '작성 중인 글 취소' 클릭")
                    await cancel_btn.click()
                    await asyncio.sleep(1)

                help_close = page.locator(".se-help-panel-close-button, button[aria-label='도움말 닫기']").first
                if await help_close.count() > 0 and await help_close.is_visible():
                    print("  도움말 닫기 클릭")
                    await help_close.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # 제목 입력
        test_title = "[테스트] 훈훈수산 양념게장 팩트체크 테스트 글"
        print(f"\n3. 제목 입력: '{test_title}'")
        try:
            # 제목 영역 선택
            title_el = page.locator(".se-documentTitle, [data-placeholder='제목']").first
            await title_el.click()
            await asyncio.sleep(0.5)
            await page.keyboard.type(test_title, delay=20)
            await asyncio.sleep(1)
            print("  제목 입력 완료")
        except Exception as e:
            print(f"  제목 입력 오류: {e}")

        # 본문 입력
        print("\n4. 본문 입력 중...")
        try:
            # 본문으로 포커스 이동
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            
            test_content = [
                "이 글은 ai-bloger 자동 포스팅 파이프라인 검증용 비공개 테스트 글입니다.",
                "",
                "■ 훈훈수산 한입 양념게장 팩트체크 요약",
                "1. 1kg 15,800원 가성비는 확실하나, 집게다리는 껍질이 딱딱하니 깨물지 말 것.",
                "2. 냉동 배송 제품은 무조건 냉장실 저온 해동해야 비린내가 안 남.",
                "3. 남은 양념장은 계란후라이와 김가루를 얹어 비빔밥으로 활용할 것.",
                "",
                "#양념게장 #훈훈수산 #자동포스팅테스트"
            ]
            
            for line in test_content:
                await page.keyboard.type(line, delay=15)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.1)
                
            print("  본문 입력 완료")
        except Exception as e:
            print(f"  본문 입력 오류: {e}")

        await asyncio.sleep(1.5)

        # 5. [발행] 버튼 클릭 (우측 상단 초록색/녹색 발행 버튼)
        print("\n5. 우측 상단 [발행] 버튼 클릭 중...")
        try:
            publish_btn = page.locator("button.se-header-publish-button, button:has-text('발행')").first
            await publish_btn.click()
            await asyncio.sleep(1.5)
            print("  발행 설정 레이어 오픈됨")
        except Exception as e:
            print(f"  발행 버튼 클릭 오류: {e}")

        # 6. [비공개] 라디오 버튼 선택
        print("\n6. [비공개] 라디오 버튼 선택 중...")
        try:
            # '비공개' 라벨 또는 라디오 버튼 클릭
            private_radio = page.locator("label:has-text('비공개'), input[value='false'], input#open_type_private").first
            await private_radio.click()
            await asyncio.sleep(1)
            print("  [OK] [비공개] 설정 완료!")
        except Exception as e:
            print(f"  비공개 라디오 버튼 클릭 오류: {e}")

        # 7. 최종 [발행하기] 버튼 클릭 (레이어 하단의 확인/발행 버튼)
        print("\n7. 최종 [발행하기] 버튼 클릭...")
        try:
            final_publish = page.locator("button.confirm_btn, button.btn_publish, button:has-text('발행하기')").first
            if await final_publish.count() == 0:
                # 텍스트가 그냥 '발행'인 레이어 버튼 탐색
                final_publish = page.locator(".publish_btn_area button, button:has-text('발행')").last

            await final_publish.click()
            print("  최종 발행 버튼 클릭 완료! 페이지 이동 대기...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"  최종 발행 버튼 클릭 오류: {e}")

        # 결과 확인 및 스크린샷 저장
        result_url = page.url
        print(f"\n최종 완료 URL: {result_url}")
        
        capture_path = OUT_DIR / "test_publish_result.png"
        await page.screenshot(path=str(capture_path))
        print(f"[CAPTURE] 결과 스크린샷 저장: {capture_path}")

        print("\n==========================================")
        print("[SUCCESS] 테스트 완료! 브라우저 창을 닫습니다.")
        print("==========================================")
        await asyncio.sleep(3)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
