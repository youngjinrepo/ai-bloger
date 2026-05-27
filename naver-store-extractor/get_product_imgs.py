# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('output/2849385212/2849385212_product.json', 'rb') as f:
    data = json.load(f)

print("상품명:", data.get("name"))
print("가격:", data.get("salePrice"))
print("제조사:", data.get("naverShoppingSearchInfo", {}).get("manufacturerName"))
print("브랜드:", data.get("naverShoppingSearchInfo", {}).get("brandName"))
print("카테고리:", data.get("category", {}).get("wholeCategoryName"))

imgs = data.get("productImages", [])
print(f"\n상품 이미지 {len(imgs)}개:")
for img in imgs:
    print(f"  {img.get('url')} ({img.get('width')}x{img.get('height')})")

opts = data.get("optionCombinations", [])
print(f"\n옵션 {len(opts)}개:")
for opt in opts:
    print(f"  {opt.get('optionName1')} / {opt.get('optionName2', '')} | 가격+{opt.get('price')} | 재고{opt.get('stockQuantity')}")

info = data.get("productInfoProvidedNoticeView", {}).get("basic", {})
for section, content in info.items():
    print(f"\n[{section}]")
    if isinstance(content, dict):
        for k, v in content.items():
            print(f"  {k}: {v}")
