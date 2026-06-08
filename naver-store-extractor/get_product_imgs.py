# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

PRODUCT_ID = sys.argv[1] if len(sys.argv) > 1 else "5538887549"

with open(f'output/{PRODUCT_ID}/{PRODUCT_ID}_product.json', 'rb') as f:
    data = json.load(f)

print("상품명:", data.get("name"))
print("가격:", data.get("salePrice"))
print("할인가:", data.get("discountedSalePrice"))
print("제조사:", data.get("naverShoppingSearchInfo", {}).get("manufacturerName"))
print("브랜드:", data.get("naverShoppingSearchInfo", {}).get("brandName"))
print("카테고리:", data.get("category", {}).get("wholeCategoryName"))

imgs = data.get("productImages", [])
print(f"\n상품 이미지 {len(imgs)}개:")
for img in imgs:
    print(f"  {img.get('url')} ({img.get('width')}x{img.get('height')})")

opts = data.get("optionCombinations", [])
print(f"\n옵션 {len(opts)}개:")
for opt in opts[:15]:
    names = " / ".join(filter(None, [opt.get("optionName1",""), opt.get("optionName2",""), opt.get("optionName3","")]))
    print(f"  {names} | +{opt.get('price')}원 | 재고{opt.get('stockQuantity')}")

info = data.get("productInfoProvidedNoticeView", {}).get("basic", {})
for section, content in info.items():
    print(f"\n[{section}]")
    if isinstance(content, dict):
        for k, v in content.items():
            if v and str(v) not in ("None", "null", ""):
                print(f"  {k}: {v}")
