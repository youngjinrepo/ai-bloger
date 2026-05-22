"""
fetch + parse 테스트 (Vision API 없음).
실행 전 python login_once.py 로 세션 저장 필요.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.fetcher import fetch_product_page
from src.parser import extract_product_id, parse_metadata

URL = sys.argv[1] if len(sys.argv) > 1 else "https://brand.naver.com/verynature/products/9440092716"


async def main():
    product_id = extract_product_id(URL)
    out_dir = Path("output") / product_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"product_id: {product_id}")
    result = await fetch_product_page(URL, out_dir)
    html = result["html"]
    screenshots = result["screenshots"]

    print("\n--- 메타데이터 파싱 ---")
    meta = parse_metadata(html)
    for k, v in meta.items():
        print(f"  {k}: {v}")

    print(f"\n스크린샷: {[str(s) for s in screenshots]}")
    print("\n[OK] fetch + parse 성공")


if __name__ == "__main__":
    asyncio.run(main())
