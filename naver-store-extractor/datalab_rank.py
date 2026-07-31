# -*- coding: utf-8 -*-
"""데이터랩 쇼핑인사이트 카테고리별 인기검색어 — 직접 JSON API 호출.
브라우저/DOM/로그인/캡차 불필요. getCategoryKeywordRank.naver POST.

사용법:
  python datalab_rank.py            # 주요 카테고리 전체 스캔
  python datalab_rank.py 50000006   # 특정 cid만
"""
import urllib.request, urllib.parse, json, sys, time
from datetime import date, timedelta
from pathlib import Path

# 1차 카테고리 cid (네이버 쇼핑 대분류)
CATEGORIES = {
    "50000000": "패션의류",
    "50000001": "패션잡화",
    "50000002": "화장품/미용",
    "50000003": "디지털/가전",
    "50000004": "가구/인테리어",
    "50000005": "출산/육아",
    "50000006": "식품",
    "50000007": "스포츠/레저",
    "50000008": "생활/건강",
    "50000009": "여가/생활편의",
}

API = "https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver"


def fetch_rank(cid, count=20, days=30):
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days)
    data = urllib.parse.urlencode({
        "cid": cid, "timeUnit": "date",
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "age": "", "gender": "", "device": "", "page": "1", "count": str(count),
    }).encode()
    req = urllib.request.Request(API, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Referer": "https://datalab.naver.com/shoppingInsight/sCategory.naver",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    })
    r = urllib.request.urlopen(req, timeout=15)
    d = json.loads(r.read().decode("utf-8"))
    return d.get("ranks", [])


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(CATEGORIES.keys())
    result = {}
    for cid in targets:
        name = CATEGORIES.get(cid, cid)
        try:
            ranks = fetch_rank(cid)
            kws = [f"{x['rank']}.{x['keyword']}" for x in ranks]
            result[name] = [x["keyword"] for x in ranks]
            line = f"[{name}] " + "  ".join(kws)
            sys.stdout.buffer.write((line + "\n\n").encode("utf-8"))
        except Exception as e:
            sys.stdout.buffer.write(f"[{name}] ERROR: {e}\n".encode("utf-8"))
        time.sleep(0.5)

    out = Path("output/datalab_ranks.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.buffer.write(f"저장: {out}\n".encode("utf-8"))


if __name__ == "__main__":
    main()
