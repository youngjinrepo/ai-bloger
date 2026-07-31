"""헤드풀 브라우저로 상품 페이지 접속. 캡차가 뜨면 사용자가 직접 풀고,
상품 API가 캡처되면 저장. IP 플래그(보안 확인) 우회용."""
import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

URL = "https://smartstore.naver.com/imnutri/products/11618484526"
PRODUCT_ID = "11618484526"
OUT_DIR = Path(f"output/{PRODUCT_ID}")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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
            if "json" in ct and (PRODUCT_ID in url or "simple-products" in url or "/products/" in url or "contents" in url):
                try:
                    body = await resp.body()
                    captured.append({"url": url, "size": len(body), "body": body})
                    print(f"[CAP] {url[:110]} ({len(body)} bytes)")
                except Exception:
                    pass

        page.on("response", on_resp)

        print("브라우저가 열립니다. 보안 확인(캡차)이 뜨면 직접 풀어주세요.")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        print(f"상품 페이지로 이동: {URL}")
        await page.goto(URL, wait_until="domcontentloaded", timeout=40000)

        # 상품 API가 잡힐 때까지 최대 10분 대기 (사용자 캡차 풀이 시간 포함)
        print("상품 데이터 대기 중... 캡차 다 풀고 상품 페이지가 뜨면 자동 저장됩니다.")
        print(">> 성공하면 이 창에 '[CAP] .../products/...' 와 '저장' 이 찍혀요. 그 전까지 브라우저 닫지 마세요. <<")
        product_found = False
        for i in range(300):  # 300 * 2s = 10분
            await asyncio.sleep(2)
            for c in captured:
                if f"/products/{PRODUCT_ID}" in c["url"] or "simple-products" in c["url"]:
                    product_found = True
                    break
            if product_found:
                print("상품 API 감지! 나머지 응답 마저 수집 중...")
                await asyncio.sleep(4)  # 나머지 API도 마저 캡처
                break
            if i % 15 == 0 and i > 0:
                print(f"  ...대기 중 ({i*2}초 경과, 캡차 계속 풀어주세요)")

        # 브라우저가 닫혀 있어도 크래시 안 나게 방어
        try:
            title = await page.title()
            print(f"\n페이지 제목: {title}")
        except Exception:
            print("\n(브라우저 창이 닫혔지만 캡처분은 저장합니다)")

        if captured:
            product_cnt = 0
            for c in sorted(captured, key=lambda x: x["size"], reverse=True):
                fname = OUT_DIR / f"cap_{c['size']}.json"
                fname.write_bytes(c["body"])
                if f"/products/{PRODUCT_ID}" in c["url"] or "simple-products" in c["url"]:
                    product_cnt += 1
                print(f"저장: {fname} ({c['size']} bytes)")
            print(f"\n상품 관련 API: {product_cnt}개 {'[성공]' if product_cnt else '[실패: 배너만 캡처, 캡차 미통과]'}")
        else:
            try:
                html = await page.content()
                (OUT_DIR / "page.html").write_text(html, encoding="utf-8")
                print("캡처 없음 - HTML 저장")
            except Exception:
                print("캡처 없음")

        try:
            await browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
