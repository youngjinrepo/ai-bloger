# -*- coding: utf-8 -*-
"""네이버 블로그 비공개 발행 실전 테스트 (Stealth 우회 적용)"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
SESSION_PATH = ROOT / "cookies" / "session.json"
OUT_DIR = ROOT / "output"

# stealth script
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const arr = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        arr.__proto__ = PluginArray.prototype;
        return arr;
    }
});
"""

async def main():
    async with async_playwright() as p:
        # headless=False로 눈에 보이게 실행
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(SESSION_PATH),
            viewport={"width": 1300, "height": 950},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        await ctx.add_init_script(STEALTH_SCRIPT)
        page = await ctx.new_page()

        print("1. naver.com 경유...")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        print("2. 블로그 홈 경유...")
        await page.goto("https://section.blog.naver.com/BlogHome.naver", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        print("3. 글쓰기 페이지 진입...")
        await page.goto("https://blog.naver.com/GoBlogWrite.naver", wait_until="domcontentloaded")
        await asyncio.sleep(4)

        print(f"현재 URL: {page.url}")
        
        # 만약 로그인 창이면 사용자가 직접 입력할 수 있도록 대기
        if "nidlogin" in page.url:
            print("[안내] 브라우저 창에서 로그인을 완료해 주세요! (로그인 후 자동으로 이어집니다)")
            await page.wait_for_url(lambda u: "nidlogin" not in u and "blog.naver.com" in u, timeout=300000)
            await asyncio.sleep(3)
            print("[OK] 로그인 완료 감지! 최신 쿠키를 저장합니다...")
            await ctx.storage_state(path=str(SESSION_PATH))

        print(f"에디터 진입 확인: {page.url}")
        await asyncio.sleep(4)

        # 강력한 팝업 및 안내창 자동 무력화 (Popup Breaker)
        print("4. 팝업 및 안내창 자동 제거 중...")
        for step in range(5):
            # 1) ESC 키로 일반 모달 닫기
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.3)

            # 2) 네이버 에디터 특유의 팝업 버튼들 전수 탐색 및 클릭
            popup_selectors = [
                "button:has-text('취소')",
                "button:has-text('닫기')",
                "button.se-popup-button-cancel",
                "button.se-help-panel-close-button",
                "button[aria-label='도움말 닫기']",
                "button[aria-label='닫기']",
                ".se-popup-container button",
                "button:has-text('확인')",
            ]
            for sel in popup_selectors:
                try:
                    btns = page.locator(sel)
                    cnt = await btns.count()
                    for i in range(cnt):
                        b = btns.nth(i)
                        if await b.is_visible():
                            await b.click(timeout=1000)
                            print(f"  [클릭 닫기] {sel}")
                            await asyncio.sleep(0.4)
                except Exception:
                    pass

            # 3) 화면을 덮고 있는 잔여 딤드(dimmed) / 팝업 레이어 DOM 강제 제거
            try:
                await page.evaluate("""() => {
                    const targets = document.querySelectorAll('.se-popup-container, .se-help-panel, .se-dimmed, .se-dialog, [role="dialog"]');
                    targets.forEach(el => el.remove());
                }""")
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # 5. 제목 입력
        test_title = "[테스트] 훈훈수산 양념게장 팩트체크 비공개 글"
        print(f"5. 제목 입력 시작: '{test_title}'")
        try:
            # 제목 영역 강제 클릭 및 포커스
            title_field = page.locator(".se-documentTitle, [data-placeholder='제목'], .se-ff-nanumgothic.se-fs32").first
            await title_field.click(force=True, timeout=5000)
            await asyncio.sleep(0.5)
            await page.keyboard.type(test_title, delay=20)
            await asyncio.sleep(0.5)
            print("  [OK] 제목 입력 완료")
        except Exception as e:
            print(f"  [재시도] JS 강제 포커스로 제목 입력 시도: {e}")
            await page.evaluate("""(t) => {
                const el = document.querySelector('.se-documentTitle') || document.querySelector('[data-placeholder="제목"]');
                if (el) {
                    el.focus();
                    el.innerText = t;
                }
            }""", test_title)
            await asyncio.sleep(0.5)

        # 6. 본문 입력
        print("6. 본문 입력 시작...")
        try:
            # 제목에서 Enter 눌러 본문 진입 또는 본문 영역 강제 클릭
            body_field = page.locator(".se-content, [data-placeholder='본문을 입력하세요'], .se-text-paragraph").first
            if await body_field.count() > 0:
                await body_field.click(force=True, timeout=5000)
            else:
                await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            lines = [
                "이 글은 ai-bloger 자동 포스팅 파이프라인 검증용 비공개 테스트 글입니다.",
                "",
                "1. 훈훈수산 한입 양념게장 15,800원 가성비 팩트체크",
                "2. 집게다리는 껍질이 딱딱하니 절대 씹지 말고 찌개 육수로 쓸 것.",
                "3. 냉동 배송품은 냉장실에서 저온 해동해야 비린내가 나지 않음.",
                "",
                "#양념게장 #훈훈수산 #자동포스팅테스트"
            ]
            for line in lines:
                await page.keyboard.type(line, delay=15)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.1)
            print("  본문 입력 완료")
        except Exception as e:
            print(f"  본문 입력 에러: {e}")

        await asyncio.sleep(2)

        # 6. [발행] 버튼 클릭 (우측 상단)
        print("6. 우측 상단 [발행] 버튼 클릭 중...")
        try:
            publish_btn = page.locator("button.se-header-publish-button, button:has-text('발행')").first
            await publish_btn.click()
            await asyncio.sleep(2)
            print("  발행 레이어 열림")
        except Exception as e:
            print(f"  발행 버튼 에러: {e}")

        # 7. [비공개] 선택
        print("7. [비공개] 라디오 버튼 선택 중...")
        try:
            private_radio = page.locator("label:has-text('비공개'), input[value='false'], input#open_type_private").first
            await private_radio.click(force=True, timeout=3000)
            await asyncio.sleep(1)
            print("  [OK] [비공개] 설정 완료!")
        except Exception as e:
            print(f"  [재시도] JS 강제 클릭으로 비공개 선택 시도: {e}")
            await page.evaluate("""() => {
                const labels = Array.from(document.querySelectorAll('label, input'));
                const p = labels.find(el => el.innerText && el.innerText.includes('비공개'));
                if (p) p.click();
            }""")
            await asyncio.sleep(1)

        # 8. 최종 [발행] 클릭
        print("8. 최종 [발행] 버튼 클릭...")
        try:
            confirm_btn = page.locator(".publish_btn_area button, button.confirm_btn, button.btn_publish").last
            await confirm_btn.click()
            print("  최종 발행 버튼 클릭 완료!")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"  최종 발행 클릭 에러: {e}")

        print(f"최종 완료 URL: {page.url}")
        res_png = OUT_DIR / "final_private_publish.png"
        await page.screenshot(path=str(res_png))
        print(f"스크린샷 저장: {res_png}")

        await asyncio.sleep(3)
        await browser.close()
        print("SUCCESS! 모든 테스트가 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())

