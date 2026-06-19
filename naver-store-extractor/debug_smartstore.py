"""디버그: smartstore.naver.com 상품 페이지 API 응답 캡처"""
import asyncio
import random
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

if len(sys.argv) >= 3:
    URL = sys.argv[1]
    PRODUCT_ID = sys.argv[2]
else:
    URL = "https://brand.naver.com/koreasusan1/products/5538887549"
    PRODUCT_ID = "5538887549"
OUT_DIR = Path(f"output/{PRODUCT_ID}")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            if "json" in ct and any(kw in url for kw in [
                PRODUCT_ID, "content", "detail", "description", "smartstore"
            ]):
                try:
                    body = await resp.body()
                    captured.append({"url": url, "size": len(body), "body": body})
                    print(f"[CAP] {url[:120]}")
                    print(f"      size={len(body)} bytes")
                except Exception:
                    pass

        page.on("response", on_resp)

        # naver.com 먼저 경유 (Referer 자연화)
        print("naver.com 경유 중...")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(random.uniform(1.5, 3.0))

        print(f"페이지 로드: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(random.uniform(2.0, 4.0))

        title = await page.title()
        print(f"\n페이지 제목: {title}")

        if not captured:
            print("\n캡처된 API 없음. 세션 만료 여부 확인 필요.")
            html = await page.content()
            Path(OUT_DIR / "page.html").write_text(html, encoding="utf-8")
            print(f"  현재 URL: {page.url}")
            await browser.close()
            return

        captured.sort(key=lambda x: x["size"], reverse=True)
        print(f"\n=== 캡처된 API 응답 {len(captured)}개 (크기 순) ===")
        for c in captured:
            print(f"  {c['size']:>8} bytes | {c['url'][:100]}")

        # 상품 API (products/{ID}?withWindow=false) 저장
        product_api = None
        for c in captured:
            if f"/products/{PRODUCT_ID}" in c["url"] and "contents" not in c["url"]:
                product_api = c
                break
        if product_api:
            p_path = OUT_DIR / f"{PRODUCT_ID}_product.json"
            p_path.write_bytes(product_api["body"])
            print(f"\n[저장] 상품 API: {p_path}")
            try:
                pd = json.loads(product_api["body"])
                # 상품명, 가격, 이미지 등 주요 정보 출력
                prod = pd.get("product", pd)
                name = prod.get("name") or prod.get("productName", "")
                price = prod.get("salePrice") or prod.get("discountedSalePrice", "")
                imgs = prod.get("productImages") or prod.get("representImages", [])
                print(f"  상품명: {name}")
                print(f"  가격: {price}")
                print(f"  이미지 수: {len(imgs) if isinstance(imgs, list) else '?'}")
                if isinstance(imgs, list):
                    for img in imgs[:3]:
                        url_ = img.get("url") or img.get("imageUrl") or img if isinstance(img, str) else ""
                        print(f"    {url_}")
            except Exception as e:
                print(f"  파싱 실패: {e}")

        # contents API 저장 (상세설명 이미지용)
        contents_api = None
        for c in captured:
            if "/contents/" in c["url"]:
                contents_api = c
                break
        if contents_api:
            c_path = OUT_DIR / f"{PRODUCT_ID}_raw.json"
            c_path.write_bytes(contents_api["body"])
            print(f"[저장] contents API: {c_path}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
