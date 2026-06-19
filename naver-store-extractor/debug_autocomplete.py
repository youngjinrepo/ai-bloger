"""네이버 자동완성 API로 연관 검색어 조회 (검색량 추정 금지, 연관어 발굴용)"""
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path

QUERIES = sys.argv[1:] or ["암꽃게", "절단꽃게", "꽃게 금어기", "꽃게장"]

results = {}
for q in QUERIES:
    encoded = urllib.parse.quote(q)
    url = f"https://ac.search.naver.com/nx/ac?q={encoded}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = [x[0] for x in data.get("items", [[]])[0]]
    results[q] = items

Path("output/autocomplete.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("saved output/autocomplete.json")
