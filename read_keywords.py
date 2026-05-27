# -*- coding: utf-8 -*-
import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print("사용법: python read_keywords.py <엑셀파일경로>")
    sys.exit(1)

wb = openpyxl.load_workbook(sys.argv[1])
ws = wb.active
rows = list(ws.iter_rows(values_only=True))

print(f"총 {len(rows)-2}개 키워드")
print("키워드 | PC검색량 | 모바일검색량 | 경쟁정도 | 월평균클릭비용")
print("---")
for r in rows[2:]:
    if r[0]:
        kw = str(r[0]).strip()
        pc = r[1]
        mob = r[2]
        comp = r[7]
        cpc = r[8]
        total = 0
        try:
            total = int(str(pc).replace(',','')) + int(str(mob).replace(',',''))
        except:
            pass
        print(f"{kw} | PC:{pc} | 모:{mob} | 합:{total} | 경쟁:{comp} | CPC:{cpc}")
