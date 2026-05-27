# -*- coding: utf-8 -*-
import json, asyncio, sys, io
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import httpx
from PIL import Image

PRODUCT_ID = "2849385212"
OUT_DIR = Path(f"output/{PRODUCT_ID}/main_imgs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

async def main():
    with open(f'output/{PRODUCT_ID}/{PRODUCT_ID}_product.json', 'rb') as f:
        data = json.load(f)

    imgs = data.get("productImages", [])
    headers = {"User-Agent": USER_AGENT, "Referer": "https://smartstore.naver.com/"}

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
        for i, img in enumerate(imgs, 1):
            url = img.get("url", "")
            try:
                r = await client.get(url)
                pil = Image.open(io.BytesIO(r.content))
                out_path = OUT_DIR / f"img_{i}.jpg"
                pil.convert("RGB").save(str(out_path))
                print(f"[{i}] {pil.width}x{pil.height} -> {out_path.name}")
            except Exception as e:
                print(f"[{i}] 실패: {e}")

asyncio.run(main())
