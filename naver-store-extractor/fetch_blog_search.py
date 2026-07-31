"""네이버 블로그 검색 결과(제목+요약) 수집 — 경쟁 후기글 구조 파악용"""
import asyncio
import json
import random
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))
from src.fetcher import USER_AGENTS, SESSION_PATH, STEALTH_SCRIPT
from playwright.async_api import async_playwright

QUERIES = sys.argv[1:] or ["닌자 블라스트 맥스 후기"]
OUT = Path("output/blog_search.json")


async def main():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            storage_state=str(SESSION_PATH),
        )
        await ctx.add_init_script(STEALTH_SCRIPT)
        page = await ctx.new_page()
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        for q in QUERIES:
            url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&query={urllib.parse.quote(q)}"
            await page.goto(url, wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(2.5)
            await page.mouse.wheel(0, 2500)
            await asyncio.sleep(1.5)
            items = await page.evaluate(
                """() => {
                    const out = [];
                    document.querySelectorAll('a').forEach(a => {
                        const t = (a.innerText || '').trim();
                        if (a.href && a.href.includes('blog.naver.com') && t.length > 8 && t.length < 120) {
                            out.push({title: t, url: a.href});
                        }
                    });
                    const texts = [];
                    document.querySelectorAll('div,span,p').forEach(e => {
                        const t = (e.innerText || '').trim();
                        if (t.length > 60 && t.length < 400 && !e.querySelector('div,p')) texts.push(t);
                    });
                    return {links: out.slice(0, 40), snippets: texts.slice(0, 30)};
                }"""
            )
            results[q] = items
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
            titles = []
            for it in items["links"]:
                if it["title"] not in titles:
                    titles.append(it["title"])
            print(f"\n===== {q} =====")
            for t in titles[:20]:
                print(" *", t.replace("\n", " / ")[:110])
            print("--- snippets ---")
            for s in items["snippets"][:10]:
                print(" -", s.replace("\n", " ")[:200])
            await asyncio.sleep(1.5)

        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nsaved {OUT}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
