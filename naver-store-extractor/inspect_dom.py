"""content API 응답 raw text 캡처 및 저장."""
import asyncio, random, sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright

URL = "https://smartstore.naver.com/sutomarket/products/4922777882"

async def main():
    captured = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR", storage_state=str(SESSION_PATH),
        )
        page = await ctx.new_page()

        async def on_resp(resp):
            if "/contents/" in resp.url and "isResponsive" in resp.url:
                print(f"  API 캡처: status={resp.status} url={resp.url[:80]}")
                try:
                    body = await resp.body()
                    captured["body"] = body
                    captured["url"] = resp.url
                    print(f"  body 길이: {len(body)} bytes")
                    print(f"  앞 500바이트: {body[:500]}")
                except Exception as e:
                    print(f"  body() 실패: {e}")

        page.on("response", on_resp)

        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await browser.close()

    if "body" in captured:
        out = Path("output/content_raw.json")
        out.write_bytes(captured["body"])
        print(f"\n저장: {out} ({len(captured['body'])} bytes)")

        try:
            data = json.loads(captured["body"])
            print(f"JSON 파싱 성공. 최상위 타입: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"최상위 키: {list(data.keys())[:20]}")
            elif isinstance(data, list):
                print(f"리스트 길이: {len(data)}, 첫번째 타입: {type(data[0]).__name__}")

            # 이미지 URL 탐색
            raw_str = captured["body"].decode("utf-8", errors="ignore")
            imgs = re.findall(r'https://shop-phinf\.pstatic\.net[^\s"\'<>\\]+', raw_str)
            print(f"\nshop-phinf URL ({len(imgs)}개):")
            for u in list(dict.fromkeys(imgs))[:10]:
                print(f"  {u}")
        except Exception as e:
            print(f"JSON 파싱 실패: {e}")
    else:
        print("content API 응답 없음")

if __name__ == "__main__":
    asyncio.run(main())
