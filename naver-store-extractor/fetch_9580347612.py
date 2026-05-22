"""Fetch product screenshots for 9580347612 (Wholeberry lemon juice)"""
import asyncio
import json
from pathlib import Path
from src.fetcher import fetch_product_page
from src.parser import parse_metadata

URL = "https://brand.naver.com/wholeberry/products/9580347612"
OUT_DIR = Path("output/9580347612")


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = await fetch_product_page(URL, OUT_DIR)
    meta = parse_metadata(result["html"])

    print("\n=== 메타데이터 ===")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\n스크린샷 {len(result['screenshots'])}장 저장 완료")
    for p in result["screenshots"]:
        print(f"  {p}")


if __name__ == "__main__":
    asyncio.run(main())
