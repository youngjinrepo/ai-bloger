"""
Vision 분석은 Claude Code가 직접 이미지를 읽고 수행합니다.
이 모듈은 분석 결과를 받아 저장하는 역할만 합니다.
"""
import json
from pathlib import Path
from datetime import datetime

from .schemas import Product, ProductDetails, Price
from .parser import extract_product_id


def save_results(
    url: str,
    meta: dict,
    details: ProductDetails,
    screenshot_paths: list[Path],
    output_dir: Path,
) -> tuple[Path, Path]:
    """분석 결과를 product.json과 product.md로 저장."""
    product_id = extract_product_id(url)

    product = Product(
        url=url,
        product_id=product_id,
        name=meta.get("name") or "(미추출)",
        brand=meta.get("brand"),
        category=meta.get("category"),
        price=meta.get("price") or Price(),
        rating=meta.get("rating"),
        review_count=meta.get("review_count"),
        main_image_url=meta.get("main_image_url"),
        details=details,
        extracted_at=datetime.now(),
        source_screenshots=[str(p) for p in screenshot_paths],
    )

    json_path = output_dir / "product.json"
    json_path.write_text(
        product.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )

    md_path = output_dir / "product.md"
    md_path.write_text(_to_markdown(product), encoding="utf-8")

    return json_path, md_path


def _to_markdown(p: Product) -> str:
    lines = [
        f"# {p.name}",
        f"",
        f"- **브랜드**: {p.brand or '-'}",
        f"- **카테고리**: {p.category or '-'}",
    ]
    if p.price.original:
        lines.append(f"- **정가**: {p.price.original:,}원")
    if p.price.sale:
        lines.append(f"- **할인가**: {p.price.sale:,}원")
    if p.rating:
        lines.append(f"- **평점**: {p.rating} ({p.review_count:,}개 리뷰)")
    lines += [f"- **URL**: {p.url}", ""]

    if p.details.features:
        lines.append("## 상품 특징")
        for f in p.details.features:
            lines.append(f"- {f}")
        lines.append("")

    if p.details.effects:
        lines.append("## 효능/영양")
        for e in p.details.effects:
            lines.append(f"- {e}")
        lines.append("")

    if p.details.specs:
        lines.append("## 규격/스펙")
        for k, v in p.details.specs.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    if p.details.storage:
        lines += ["## 보관법", p.details.storage, ""]

    if p.details.caution:
        lines += ["## 주의사항", p.details.caution, ""]

    lines += [f"---", f"*추출일시: {p.extracted_at.strftime('%Y-%m-%d %H:%M')}*"]
    return "\n".join(lines)
