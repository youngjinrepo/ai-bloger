import asyncio
import sys
from pathlib import Path

from .config import OUTPUT_DIR
from .fetcher import fetch_product_page
from .parser import extract_product_id, parse_metadata


def run(url: str) -> None:
    asyncio.run(_process(url))


async def _process(url: str) -> None:
    print(f"\n=== 추출 시작 ===")
    print(f"URL: {url}")

    product_id = extract_product_id(url)
    product_dir = OUTPUT_DIR / product_id
    product_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = await fetch_product_page(url, product_dir)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    html = result["html"]
    screenshot_paths = result["screenshots"]

    print("  [parse] 메타데이터 파싱...")
    meta = parse_metadata(html)

    print(f"\n=== 완료 ===")
    print(f"  상품명: {meta.get('name', '(미추출)')}")
    print(f"  가격: {meta.get('price', {})}")
    print(f"  스크린샷: {len(screenshot_paths)}장")
    for p in screenshot_paths:
        print(f"    {p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python -m src.main <URL>")
        sys.exit(1)
    run(sys.argv[1])
