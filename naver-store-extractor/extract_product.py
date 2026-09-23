import requests
import json
import re
import sys
import os

url = "https://brand.naver.com/babionkorea/products/455882425"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
html = r.text

m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?})</script>', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    os.makedirs("output/455882425", exist_ok=True)
    with open("output/455882425/455882425_product.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to output/455882425/455882425_product.json")
else:
    print("Not found __PRELOADED_STATE__")
    with open("output/455882425_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved debug html")

