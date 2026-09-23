# -*- coding: utf-8 -*-
"""네이버 블로그 스마트에디터 ONE 자동 임시저장 스크립트

사용법:
  python blog-writing/naver_auto_poster.py blog-writing/final/4772009430_final.md
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent.parent
SESSION_PATH = ROOT / "cookies" / "session.json"


def parse_final_markdown(md_path: Path):
    """최종 마크다운 파일에서 제목, 본문, 태그, 사진 정보 추출"""
    text = md_path.read_text(encoding="utf-8")

    # 1. 추천 제목 추출
    title = ""
    title_match = re.search(r"## 제목.*?\n(.*?)\n---", text, re.DOTALL)
    if title_match:
        for line in title_match.group(1).split("\n"):
            if "← 추천" in line or "1." in line:
                # 번호, 불릿, 마크다운 제거
                clean = re.sub(r"^\d+\.\s*|\*\*|←\s*추천", "", line).strip()
                if clean:
                    title = clean
                    break
    if not title:
        first_line = text.split("\n")[0]
        title = re.sub(r"^#\s*", "", first_line).strip()

    # 2. 본문 추출
    body_match = re.search(r"## 본문\s*\n(.*?)(?:\(공백 포함|## 사진|\Z)", text, re.DOTALL)
    raw_body = body_match.group(1).strip() if body_match else text

    # 3. 태그 추출
    tags = []
    tag_match = re.search(r"## .*?태그.*?\n(.*?)(?:\Z|##)", text, re.DOTALL)
    if tag_match:
        tags = re.findall(r"#([\w가-힣]+)", tag_match.group(1))

    # 본문 단락 분리 (소제목, 문단)
    paragraphs = []
    for chunk in raw_body.split("\n\n"):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("---"):
            continue
        # 소제목 여부 확인
        if chunk.startswith("###") or chunk.startswith("##"):
            clean_sub = re.sub(r"^#+\s*", "", chunk).strip()
            paragraphs.append({"type": "subtitle", "text": clean_sub})
        else:
            paragraphs.append({"type": "text", "text": chunk})

    return {
        "title": title,
        "paragraphs": paragraphs,
        "tags": tags,
    }


async def post_to_naver_blog(article_data: dict, headless: bool = False):
    """Playwright를 이용해 스마트에디터 ONE에 입력 후 '임시저장'"""
    if not SESSION_PATH.exists():
        print(f"[ERROR] 세션 파일이 없습니다: {SESSION_PATH}")
        print("  python naver-store-extractor/login_once.py 를 먼저 실행해 로그인하세요.")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        ctx = await browser.new_context(
            storage_state=str(SESSION_PATH),
            viewport={"width": 1300, "height": 950},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        page = await ctx.new_page()

        print("1. 네이버 블로그 글쓰기 페이지 접속 중...")
        await page.goto("https://blog.naver.com/GoBlogWrite.naver", wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(4)

        if "nidlogin" in page.url:
            print("[ERROR] 로그인 세션이 만료되었습니다. 재로그인이 필요합니다.")
            await browser.close()
            return False

        print(f"  현재 접속 URL: {page.url}")

        # 팝업 닫기 (작성 중인 글 취소, 스마트에디터 안내 등)
        try:
            # "작성 중인 글이 있습니다" 취소 버튼 클릭
            cancel_btn = page.locator("button:has-text('취소')").first
            if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
                print("  '작성 중인 글 취소' 버튼 클릭")
                await cancel_btn.click()
                await asyncio.sleep(1)

            # 도움말 닫기 버튼
            help_close = page.locator(".se-help-panel-close-button, button[aria-label='도움말 닫기']").first
            if await help_close.count() > 0 and await help_close.is_visible():
                print("  도움말 닫기 클릭")
                await help_close.click()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"  팝업 처리 예외 (무시): {e}")

        # 2. 제목 입력
        print(f"2. 제목 입력 중: '{article_data['title']}'")
        try:
            # 제목 필드 찾기
            title_field = page.locator(".se-documentTitle, .se-ff-nanumgothic.se-fs32, [data-placeholder='제목']").first
            await title_field.click()
            await asyncio.sleep(0.5)
            await page.keyboard.type(article_data['title'], delay=30)
            await asyncio.sleep(1)
            print("  제목 입력 완료")
        except Exception as e:
            print(f"  [FAIL] 제목 입력 실패: {e}")

        # 3. 본문 입력
        print("3. 본문 단락 입력 중...")
        try:
            # 본문 첫 번째 단락으로 포커스 이동 (Tab 또는 본문 클릭)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)

            for i, p_info in enumerate(article_data["paragraphs"]):
                txt = p_info["text"]
                if p_info["type"] == "subtitle":
                    # 소제목 구분선 느낌 주기
                    await page.keyboard.type(f"■ {txt}", delay=20)
                else:
                    # 일반 텍스트
                    lines = txt.split("\n")
                    for line in lines:
                        clean_line = line.strip()
                        # 볼드체 등 마크다운 기호 제거
                        clean_line = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_line)
                        if clean_line:
                            await page.keyboard.type(clean_line, delay=15)
                            await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.2)

            print("  본문 입력 완료")
        except Exception as e:
            print(f"  [FAIL] 본문 입력 실패: {e}")

        # 4. 임시저장 버튼 클릭
        print("4. '저장' (임시저장) 버튼 클릭 중...")
        saved = False
        try:
            # 저장 버튼 탐색 (상단 우측 '저장' 버튼)
            save_btn = page.locator("button.se-save-button, button:has-text('저장')").first
            if await save_btn.count() > 0:
                await save_btn.click()
                await asyncio.sleep(2)
                print("  [SUCCESS] 임시저장 버튼 클릭 성공!")
                saved = True
            else:
                print("  [WARN] 저장 버튼을 찾지 못했습니다.")
        except Exception as e:
            print(f"  [FAIL] 저장 버튼 클릭 실패: {e}")

        # 스크린샷 캡처
        screenshot_path = ROOT / "output" / "naver_blog_saved.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"  결과 스크린샷 저장: {screenshot_path}")

        await browser.close()
        return saved


def main():
    if len(sys.argv) < 2:
        print("사용법: python naver_auto_poster.py <마크다운파일경로>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"파일을 찾을 수 없습니다: {md_path}")
        sys.exit(1)

    print(f"=== 마크다운 파싱: {md_path.name} ===")
    article = parse_final_markdown(md_path)
    print(f"추출된 제목: {article['title']}")
    print(f"본문 단락 수: {len(article['paragraphs'])}개")
    print(f"추출된 태그: {', '.join(article['tags'][:5])} 등 {len(article['tags'])}개\n")

    # 자동 업로드 실행
    res = asyncio.run(post_to_naver_blog(article, headless=True))
    if res:
        print("\n🎉 [성공] 네이버 블로그에 '임시저장'되었습니다! 블로그에서 확인 후 발행하세요.")
    else:
        print("\n⚠️ [실패] 임시저장 중 문제가 발생했습니다.")


if __name__ == "__main__":
    main()

