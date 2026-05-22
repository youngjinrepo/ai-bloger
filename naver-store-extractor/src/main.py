import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import OUTPUT_DIR
from .fetcher import fetch_product_page
from .parser import extract_product_id, parse_metadata
from .schemas import Product, ProductDetails
from .vision import extract_details_from_screenshots


def run(url: str) -> None:
    asyncio.run(_process(url))


async def _process(url: str) -> None:
    print(f"\n=== 추출 시작 ===")
    print(f"URL: {url}")

    product_id = extract_product_id(url)
    product_dir = OUTPUT_DIR / product_id
    product_dir.mkdir(parents=True, exist_ok=True)

    # 1. 페이지 수집
    try:
        result = await fetch_product_page(url, product_dir)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    html = result["html"]
    screenshot_paths = result["screenshots"]

    # 2. 메타데이터 파싱
    print("  [parse] 메타데이터 파싱...")
    meta = parse_metadata(html)

    # 3. Vision 추출
    details = extract_details_from_screenshots(screenshot_paths)

    # 4. 모델 조립
    product = Product(
        url=url,
        product_id=product_id,
        name=meta.get("name") or "(미추출)",
        brand=meta.get("brand"),
        category=meta.get("category"),
        price=meta.get("price") or {},
        rating=meta.get("rating"),
        review_count=meta.get("review_count"),
        main_image_url=meta.get("main_image_url"),
        details=details,
        extracted_at=datetime.now(),
        source_screenshots=[str(p) for p in screenshot_paths],
    )

    # 5. 저장
    json_path = product_dir / "product.json"
    json_path.write_text(
        product.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )

    md_path = product_dir / "product.md"
    md_path.write_text(_to_markdown(product), encoding="utf-8")

    print(f"\n=== 완료 ===")
    print(f"  JSON: {json_path}")
    print(f"  MD  : {md_path}")
    print(f"  스크린샷: {len(screenshot_paths)}장")
    _print_summary(product)


def _to_markdown(p: Product) -> str:
    lines = [
        f"# {p.name}",
        f"",
        f"- **브랜드**: {p.brand or '-'}",
        f"- **카테고리**: {p.category or '-'}",
        f"- **정가**: {p.price.original:,}원" if p.price.original else "- **정가**: -",
        f"- **할인가**: {p.price.sale:,}원" if p.price.sale else "- **할인가**: -",
        f"- **평점**: {p.rating} ({p.review_count:,}개)" if p.rating else "- **평점**: -",
        f"- **URL**: {p.url}",
        f"",
        f"## 상품 특징",
    ]
    for feat in p.details.features:
        lines.append(f"- {feat}")

    if p.details.ingredients:
        lines += ["", "## 성분/원재료"]
        for ing in p.details.ingredients:
            lines.append(f"- {ing}")

    if p.details.effects:
        lines += ["", "## 효능/효과"]
        for eff in p.details.effects:
            lines.append(f"- {eff}")

    if p.details.specs:
        lines += ["", "## 규격/스펙"]
        for k, v in p.details.specs.items():
            lines.append(f"- **{k}**: {v}")

    if p.details.usage:
        lines += ["", "## 사용법", p.details.usage]

    if p.details.storage:
        lines += ["", "## 보관법", p.details.storage]

    if p.details.caution:
        lines += ["", "## 주의사항", p.details.caution]

    lines += ["", f"---", f"*추출일시: {p.extracted_at.strftime('%Y-%m-%d %H:%M')}*"]
    return "\n".join(lines)


def _print_summary(p: Product) -> None:
    print(f"\n  상품명: {p.name}")
    print(f"  가격: {p.price.sale:,}원" if p.price.sale else "  가격: 미추출")
    print(f"  특징: {len(p.details.features)}개 추출")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python -m src.main <URL>")
        sys.exit(1)
    run(sys.argv[1])
