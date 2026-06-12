"""Download and chunk product images from captured raw JSON."""
import asyncio
import json
import re
import io
import random
import sys
from pathlib import Path

import httpx
from PIL import Image

from src.fetcher import USER_AGENTS

PRODUCT_ID = sys.argv[1] if len(sys.argv) > 1 else "7515598524"
RAW_JSON = Path(f"output/{PRODUCT_ID}/{PRODUCT_ID}_raw.json")
OUT_DIR = Path(f"output/{PRODUCT_ID}")
CHUNK_HEIGHT = 4000


def parse_images(body: bytes) -> list[str]:
    data = json.loads(body)
    render_html = data.get("renderContent", "")

    raw_urls = re.findall(r"https://shop-phinf\.pstatic\.net[^\"'<>\s\\]+", render_html)
    seen: set[str] = set()
    result: list[str] = []
    for u in raw_urls:
        u = u.split("&")[0]
        base = u.split("?")[0]
        if base and base not in seen:
            seen.add(base)
            result.append(base)
    return result


async def download_and_chunk(img_urls: list[str], output_dir: Path) -> list[Path]:
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
                images.append(img)
                print(f"  [{i+1}/{len(img_urls)}] {img.width}x{img.height}px")
            except Exception as e:
                print(f"  [FAIL] {url[:60]}: {e}")

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
        print(f"  chunk {i}: {width}x{h}px → {path.name}")
        y += CHUNK_HEIGHT
        i += 1

    return paths


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    body = RAW_JSON.read_bytes()
    urls = parse_images(body)
    print(f"Found {len(urls)} unique image URLs")
    for u in urls:
        print(f"  {u}")

    print("\nDownloading...")
    paths = await download_and_chunk(urls, OUT_DIR)
    print(f"\nDone: {len(paths)} screenshot chunks saved")


if __name__ == "__main__":
    asyncio.run(main())
