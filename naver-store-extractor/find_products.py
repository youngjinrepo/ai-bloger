"""키워드로 네이버 쇼핑 검색 → smartstore/brand 상품 링크 추출"""
import asyncio, random, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.fetcher import USER_AGENTS, SESSION_PATH
from playwright.async_api import async_playwright

KW = sys.argv[1] if len(sys.argv) > 1 else "샤인머스캣"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        kw = dict(user_agent=random.choice(USER_AGENTS), viewport={"width":1280,"height":2000},
                  locale="ko-KR", timezone_id="Asia/Seoul")
        if SESSION_PATH.exists(): kw["storage_state"]=str(SESSION_PATH)
        ctx = await browser.new_context(**kw)
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = await ctx.new_page()
        url = f"https://search.shopping.naver.com/search/all?query={urllib.parse.quote(KW)}&sort=rel"
        await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.5)
        try:
            await page.goto(url, wait_until="networkidle", timeout=40000)
        except Exception as e: print("warn", e)
        for _ in range(5):
            await page.mouse.wheel(0,3000); await asyncio.sleep(1)
        links = await page.evaluate("""() => {
            const out=[];
            document.querySelectorAll('a').forEach(a=>{
              const h=a.href||'';
              if((h.includes('brand.naver.com')||h.includes('smartstore.naver.com'))&&h.includes('/products/')){
                const t=(a.innerText||'').trim().slice(0,60);
                out.push({h,t});
              }
            });
            return out;
        }""")
        seen=set(); uniq=[]
        for l in links:
            base=l['h'].split('?')[0]
            if base in seen: continue
            seen.add(base); uniq.append((base,l['t']))
        print(f"=== {KW}: {len(uniq)} products ===")
        for b,t in uniq[:25]:
            print(b, '|', t.replace('\n',' '))
        await browser.close()

asyncio.run(main())
