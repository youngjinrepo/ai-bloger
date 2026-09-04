# -*- coding: utf-8 -*-
"""아이템 발굴 자동화 — 데이터랩 급상승 → 자동완성 깊이 → 점수화 → 히스토리 저장

사용법:
  python discover.py              # 전체 실행
  python discover.py --top 15     # 후보 15개까지 자동완성 조회 (기본 20)
  python discover.py --no-ac      # 자동완성 생략 (데이터랩만, 빠름)
  python discover.py --history    # 지난 기록만 보기

결과 저장:
  history/discover/YYYY-MM-DD.json   원본 데이터
  history/discover/YYYY-MM-DD.md     사람이 읽는 요약
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datalab_rank import fetch_rank, CATEGORIES

ROOT = Path(__file__).parent.parent
HIST = ROOT / "history" / "discover"

# 구매 직전 검색 — 살 사람이 치는 말. 클릭·전환으로 이어진다
BUY_SUFFIX = re.compile(
    r"가격|추천|후기|내돈내산|비교|순위|최저가|할인|1kg|2kg|세트|정품|당일배송|어디서"
)
# 정보 탐색 — 글감은 되지만 정보만 얻고 나갈 수 있다
INFO_SUFFIX = re.compile(
    r"차이|고르는|고르기|손질|보관|효능|부작용|만들기|레시피|"
    r"시기|제철|사용법|세척|해동|굽는|찌는|먹는법|뜻|종류|언제|방법"
)
NOISE = re.compile(r"렌탈|대여|중고|알바|채용|주가|뜻풀이")
# 블로그 상품 리뷰로 쓸 수 없는 것들 (리뷰가 없거나 제휴 불가)
EXCLUDE = re.compile(r"상품권|기프티콘|기프트카드|쿠폰|캐시|포인트|이용권|입장권|렌트|숙박권")


def autocomplete(q, timeout=8):
    e = urllib.parse.quote(q)
    url = (f"https://ac.search.naver.com/nx/ac?q={e}&con=1&frm=nv&ans=2&r_format=json"
           f"&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://search.naver.com/"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
        return [x[0] for x in d.get("items", [[]])[0]]
    except Exception:
        return []


def rising_keywords(retries=3):
    """카테고리별 7일 vs 30일 순위 비교 → 급상승 추출"""
    out = []
    for cid, name in CATEGORIES.items():
        r7 = r30 = None
        for i in range(retries):
            try:
                r7 = fetch_rank(cid, count=50, days=7)
                time.sleep(0.5)
                r30 = fetch_rank(cid, count=50, days=30)
                break
            except Exception as e:
                if i == retries - 1:
                    print(f"  [{name}] 실패: {str(e)[:40]}")
                time.sleep(2)
        if not r7:
            continue
        m7 = {x["keyword"]: x["rank"] for x in r7}
        m30 = {x["keyword"]: x["rank"] for x in r30}
        for k, r in m7.items():
            old = m30.get(k)
            if old is None and r <= 35:
                out.append({"cat": name, "kw": k, "rank": r, "prev": None, "delta": None, "type": "NEW"})
            elif old is not None and old - r >= 5:
                out.append({"cat": name, "kw": k, "rank": r, "prev": old, "delta": old - r, "type": "UP"})
        print(f"  [{name}] 급상승 {sum(1 for x in out if x['cat']==name)}건")
        time.sleep(0.5)
    return out


def load_history(exclude_date=None):
    """과거 발굴 기록 → {키워드: [날짜, ...]}   (오늘 기록은 제외해야 자기 참조가 안 생김)"""
    seen = {}
    if not HIST.exists():
        return seen
    for f in sorted(HIST.glob("*.json")):
        if exclude_date and f.stem == exclude_date:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for it in d.get("candidates", []):
            seen.setdefault(it["kw"], []).append(d.get("date", f.stem))
    return seen


def score(item, ac, history):
    """점수 = 상승세 + 검색 깊이 + 정보성 의도 + 연속성"""
    s, why = 0.0, []
    if item["type"] == "NEW":
        s += 3; why.append("신규진입 +3")
    else:
        d = min(item["delta"], 20) * 0.5
        s += d; why.append(f"{item['prev']}→{item['rank']} +{d:.1f}")

    if item["rank"] <= 5:
        s += 2; why.append(f"현재 {item['rank']}위 +2")

    if ac is None:
        why.append("자동완성 미조회")
        ac = []
    else:
        n = len(ac)
        s += min(n, 10) * 0.3
        why.append(f"자동완성 {n}개 +{min(n,10)*0.3:.1f}")
        if n == 0:
            s -= 5; why.append("자동완성 없음 -5")

    buy = [a for a in ac if BUY_SUFFIX.search(a)]
    s += len(buy) * 1.5
    if buy:
        why.append(f"구매의도 {len(buy)}개 +{len(buy)*1.5:.1f}")

    info = [a for a in ac if INFO_SUFFIX.search(a) and a not in buy]
    s += len(info) * 0.6
    if info:
        why.append(f"정보성 {len(info)}개 +{len(info)*0.6:.1f}")

    # 정보 검색만 있고 구매 검색이 없으면 감점 — 읽고 나가는 글이 된다
    if info and not buy:
        s -= 2; why.append("구매의도 없음 -2")

    if any(NOISE.search(a) for a in ac):
        s -= 2; why.append("렌탈/대여 위주 -2")

    past = history.get(item["kw"], [])
    if past:
        s += 4; why.append(f"연속상승({len(past)}회) +4")

    return round(s, 1), why, buy, info, past


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--no-ac", action="store_true")
    ap.add_argument("--history", action="store_true")
    args = ap.parse_args()

    today = date.today().isoformat()
    history = load_history(exclude_date=today)
    if args.history:
        print(f"기록된 발굴 회차: {len(list(HIST.glob('*.json'))) if HIST.exists() else 0}")
        rep = sorted(((len(v), k, v) for k, v in history.items()), reverse=True)
        print("\n반복 등장 키워드:")
        for cnt, k, dates in rep[:25]:
            if cnt > 1:
                print(f"  {cnt}회  {k:<16} {', '.join(dates)}")
        return

    print("1) 데이터랩 급상승 수집")
    items = rising_keywords()
    print(f"   총 {len(items)}건\n")

    # 제외 대상 걸러내기
    items = [x for x in items if not EXCLUDE.search(x["kw"])]
    print(f"   제외 후 {len(items)}건")

    targets = [] if args.no_ac else items
    print(f"2) 자동완성 조회 ({len(targets)}건 전량)")
    for it in items:
        it["ac"] = None          # None = 미조회, [] = 조회했으나 없음
    for it in targets:
        it["ac"] = autocomplete(it["kw"])
        time.sleep(0.2)
    print()

    print("3) 점수화")
    for it in items:
        it["score"], it["why"], it["buy"], it["info"], it["past"] = score(it, it.get("ac"), history)
    items.sort(key=lambda x: -x["score"])

    HIST.mkdir(parents=True, exist_ok=True)
    payload = {"date": today, "generated": datetime.now().isoformat(timespec="seconds"),
               "candidates": items}
    (HIST / f"{today}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"# 아이템 발굴 — {today}", "",
             f"수집 {len(items)}건 / 자동완성 조회 {len(targets)}건", "",
             "## 후보 순위", "",
             "| 점수 | 키워드 | 카테고리 | 상승 | 자동완성 | 구매의도 접미어 |",
             "|---|---|---|---|---|---|"]
    for it in items[:25]:
        mv = "NEW" if it["type"] == "NEW" else f"{it['prev']}→{it['rank']}"
        info = ", ".join(x for x in it["buy"][:3]) if it["buy"] else ("(정보성만) " + ", ".join(it["info"][:2]) if it["info"] else "-")
        star = " ⭐" if it["past"] else ""
        lines.append(f"| {it['score']}{star} | {it['kw']} | {it['cat']} | {mv} | {len(it.get('ac') or [])} | {info} |")
    lines += ["", "⭐ = 이전 회차에도 올라온 키워드 (연속 상승)", "", "## 판단 근거", ""]
    for it in items[:10]:
        lines.append(f"- **{it['kw']}** ({it['score']}점) — {' / '.join(it['why'])}")
    (HIST / f"{today}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n저장: history/discover/{today}.json / .md\n")
    print("=== 상위 12 ===")
    for it in items[:12]:
        mv = "NEW" if it["type"] == "NEW" else f"{it['prev']}→{it['rank']}"
        star = " ⭐연속" if it["past"] else ""
        print(f"  {it['score']:>5}  {it['kw']:<14} [{it['cat']}] {mv} ac={len(it.get('ac') or [])}{star}")


if __name__ == "__main__":
    main()
