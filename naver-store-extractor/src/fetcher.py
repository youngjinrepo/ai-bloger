import asyncio
import random
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright, Page

from .config import BASE_DIR

SESSION_PATH = BASE_DIR / "cookies" / "session.json"
CHUNK_HEIGHT = 4000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# 봇 탐지 우회 init script — 모든 페이지 컨텍스트에 주입
STEALTH_SCRIPT = """
// webdriver 플래그 제거
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Chrome 런타임 객체 주입
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };

// 언어 설정
Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });

// 플러그인 목록 (빈 배열 → 봇 신호, fake 플러그인 추가)
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

// permissions.query 재정의 (headless 탐지 우회)
const origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (params) => (
    params.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(params)
);

// 하드웨어 설정
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

// WebGL 벤더/렌더러 스푸핑
const getParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Intel Inc.';
    if (p === 37446) return 'Intel Iris OpenGL Engine';
    return getParam.call(this, p);
};
"""


async def fetch_product_page(url: str, output_dir: Path) -> dict:
    if not SESSION_PATH.exists():
        raise RuntimeError(
            f"세션 파일 없음: {SESSION_PATH}\n"
            "먼저 python login_once.py 를 실행하세요."
        )

    content_body: bytes | None = None
    html = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            storage_state=str(SESSION_PATH),
        )
        await context.add_init_script(STEALTH_SCRIPT)
        page = await context.new_page()

        # content API 응답 body 캡처
        async def on_response(resp):
            nonlocal content_body
            if "/contents/" in resp.url and "isResponsive" in resp.url:
                try:
                    content_body = await resp.body()
                    print(f"  [fetch] content API 캡처 ({len(content_body)} bytes)")
                except Exception:
                    pass

        page.on("response", on_response)

        # naver.com 경유 후 상품 페이지 이동 (레퍼러 자연스럽게)
        print(f"  [fetch] naver.com 경유 중...")
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(random.uniform(1.0, 2.5))

        print(f"  [fetch] 페이지 로드 중: {url}")
        await page.goto(url, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(random.uniform(1.5, 3.0))  # async response handlers 완료 대기

        if await _is_login_page(page):
            await browser.close()
            raise RuntimeError("세션 만료. python login_once.py 재실행 필요.")
        if "products" not in page.url:
            await browser.close()
            raise RuntimeError(f"상품 페이지 로드 실패: {page.url}")

        html = await page.content()
        await browser.close()

    # content body 디버그 저장
    if content_body:
        (output_dir / "content_raw.json").write_bytes(content_body)

    # 상세이미지 URL 추출
    img_urls = _parse_detail_images(content_body)
    print(f"  [fetch] 상세이미지 {len(img_urls)}개")

    screenshots = []
    if img_urls:
        screenshots = await _download_and_chunk(img_urls, output_dir)
    else:
        print("  [fetch] 상세이미지 없음")

    return {"html": html, "screenshots": screenshots}


def _parse_detail_images(body: bytes | None) -> list[str]:
    """content API 응답 body에서 상세설명 이미지 URL 파싱."""
    if not body:
        return []
    try:
        data = json.loads(body)
    except Exception:
        return []

    render_html = data.get("renderContent", "")
    if not render_html:
        return []

    raw_urls: list[str] = []

    # 분기 1: src="..." 속성 추출 — shopping-phinf (신형 CDN, 상품 상세 에디터 방식)
    raw_urls += re.findall(r'src="(https://shopping-phinf\.pstatic\.net[^"<>\s]+)"', render_html)

    # 분기 2: bare URL 추출 — shop-phinf (구형 CDN, HTML entity 포함 케이스)
    raw_urls += re.findall(r'https://shop-phinf\.pstatic\.net[^"\'<>\s\\]+', render_html)

    seen: set[str] = set()
    result: list[str] = []
    for u in raw_urls:
        # HTML entity 디코딩 (&quot; 등 제거)
        u = u.split("&")[0]
        # ?type=... 리사이즈 파라미터 제거 → 원본 이미지
        base = u.split("?")[0]
        if base and base not in seen:
            seen.add(base)
            result.append(base)

    return result


async def _download_and_chunk(img_urls: list[str], output_dir: Path) -> list[Path]:
    """이미지 다운로드 → 세로 이어붙이기 → CHUNK_HEIGHT 분할 저장."""
    import httpx
    from PIL import Image
    import io

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://smartstore.naver.com/",
    }

    images = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
        for i, url in enumerate(img_urls):
            try:
                r = await client.get(url)
                img = Image.open(io.BytesIO(r.content)).convert("RGBA").convert("RGB")
                if img.width <= 2 or img.height <= 2:
                    continue  # 트래킹 픽셀 제외
                images.append(img)
                print(f"  [fetch] 이미지 {i+1}/{len(img_urls)}: {img.width}x{img.height}px")
            except Exception as e:
                print(f"  [fetch] 다운로드 실패 ({url[:60]}): {e}")

    if not images:
        return []

    width = max(img.width for img in images)
    total_h = sum(img.height for img in images)

    canvas = Image.new("RGB", (width, total_h), "white")
    y = 0
    for img in images:
        canvas.paste(img, (0, y))
        y += img.height

    paths, y, i = [], 0, 1
    while y < total_h:
        h = min(CHUNK_HEIGHT, total_h - y)
        chunk = canvas.crop((0, y, width, y + h))
        path = output_dir / f"screenshot_{i}.png"
        chunk.save(str(path))
        paths.append(path)
        print(f"  [fetch] 청크 {i}: {width}x{h}px -> {path.name}")
        y += CHUNK_HEIGHT
        i += 1

    return paths


async def _is_login_page(page: Page) -> bool:
    return "nidlogin" in page.url
