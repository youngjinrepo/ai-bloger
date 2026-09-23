import asyncio
from pathlib import Path
from src.fetcher import fetch_product_page
import json
from src.parser import parse_metadata

URL = "https://brand.naver.com/babionkorea/products/455882425"
OUT_DIR = Path("output/455882425")

async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = await fetch_product_page(URL, OUT_DIR)
    meta = parse_metadata(result["html"])

    print("\n=== 메타데이터 ===")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\n스크린샷 {len(result.get('screenshots', []))}장 저장 완료")
    for p in result.get("screenshots", []):
        print(f"  {p}")

    with open(OUT_DIR / "455882425_product.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())

