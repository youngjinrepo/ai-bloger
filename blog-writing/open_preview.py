# -*- coding: utf-8 -*-
"""네이버 블로그 복사용 로컬 HTML 뷰어 자동 실행기

마크다운 글을 네이버 스마트에디터에 가장 잘 붙는 서식으로 브라우저에 띄웁니다.
브라우저에서 [Ctrl+A] -> [Ctrl+C] -> 네이버 블로그에 [Ctrl+V] 하시면 끝납니다.
"""
import re
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent


def markdown_to_clean_preview(md_path: Path):
    text = md_path.read_text(encoding="utf-8")

    # 제목 추출
    title = ""
    title_match = re.search(r"## 제목.*?\n(.*?)\n---", text, re.DOTALL)
    if title_match:
        for line in title_match.group(1).split("\n"):
            if "← 추천" in line or "1." in line:
                title = re.sub(r"^\d+\.\s*|\*\*|←\s*추천", "", line).strip()
                if title:
                    break
    if not title:
        title = re.sub(r"^#\s*", "", text.split("\n")[0]).strip()

    # 본문 추출
    body_match = re.search(r"## 본문\s*\n(.*?)(?:\(공백 포함|## 사진|\Z)", text, re.DOTALL)
    raw_body = body_match.group(1).strip() if body_match else text

    # 태그 추출
    tags = ""
    tag_match = re.search(r"## .*?태그.*?\n(.*?)(?:\Z|##)", text, re.DOTALL)
    if tag_match:
        tag_list = re.findall(r"#([\w가-힣]+)", tag_match.group(1))
        tags = " ".join([f"#{t}" for t in tag_list])

    # HTML 변환 (네이버 스마트에디터가 복사-붙여넣기 시 100% 인식하는 CSS 구조)
    body_html = []
    for chunk in raw_body.split("\n\n"):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("---"):
            continue

        if chunk.startswith("###"):
            sub = re.sub(r"^###\s*", "", chunk).strip()
            body_html.append(f'<h3 style="font-size: 20px; font-weight: bold; color: #111; margin-top: 30px; margin-bottom: 12px;">■ {sub}</h3>')
        elif chunk.startswith("##"):
            sub = re.sub(r"^##\s*", "", chunk).strip()
            body_html.append(f'<h2 style="font-size: 22px; font-weight: bold; color: #000; margin-top: 35px; margin-bottom: 15px;">{sub}</h2>')
        else:
            p = chunk
            p = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", p)
            p = p.replace("\n", "<br>")
            body_html.append(f'<p style="font-size: 16px; line-height: 1.9; color: #333; margin-bottom: 16px;">{p}</p>')

    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Nanum Gothic", "Malgun Gothic", sans-serif;
    max-width: 780px;
    margin: 40px auto;
    padding: 20px 40px;
    background: #f8f9fa;
  }}
  .guide-box {{
    background: #e8f5e9;
    border: 2px solid #4caf50;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 30px;
  }}
  .copy-target {{
    background: #fff;
    padding: 40px 50px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  .info-tag {{
    display: inline-block;
    background: #eee;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 13px;
    color: #555;
    margin-bottom: 10px;
  }}
</style>
</head>
<body>

<div class="guide-box">
  <h3 style="margin-top:0; color:#2e7d32;">📋 네이버 블로그 붙여넣기 가이드 (보호조치 위험 0%)</h3>
  <p style="margin: 6px 0; font-size: 15px;">1. 아래 <strong>[본문 영역]</strong> 아무 곳이나 클릭한 뒤 <strong>Ctrl + A</strong> (전체 선택) → <strong>Ctrl + C</strong> (복사) 하세요.</p>
  <p style="margin: 6px 0; font-size: 15px;">2. 평소 쓰시는 정상 브라우저에서 네이버 블로그 글쓰기를 열고 <strong>Ctrl + V</strong> 누르면 소제목 서식과 줄바꿈이 완벽하게 들어갑니다!</p>
</div>

<div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ddd;">
  <span class="info-tag">📌 추천 제목 (클릭해서 복사)</span>
  <input type="text" value="{title}" readonly style="width: 100%; font-size: 18px; font-weight: bold; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;" onclick="this.select(); document.execCommand('copy'); alert('제목이 복사되었습니다!');">
</div>

<div class="copy-target" id="content">
  <span class="info-tag">📝 본문 영역 (여기서 Ctrl+A 후 Ctrl+C)</span>
  <hr style="border: none; border-top: 1px solid #eee; margin: 15px 0 25px 0;">
  {"".join(body_html)}
  <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0 20px 0;">
  <p style="font-size: 14px; color: #666;"><strong>태그:</strong> {tags}</p>
</div>

</body>
</html>"""

    preview_path = ROOT / "output" / "blog_preview.html"
    preview_path.write_text(full_html, encoding="utf-8")
    return preview_path


def main():
    if len(sys.argv) < 2:
        target = ROOT / "blog-writing" / "final" / "4772009430_final.md"
    else:
        target = Path(sys.argv[1])

    preview_file = markdown_to_clean_preview(target)
    print(f"\n[OK] 미리보기 웹페이지 생성 완료: {preview_file}")
    print("사용자분의 기본 웹브라우저로 창을 엽니다...")
    webbrowser.open(str(preview_file))


if __name__ == "__main__":
    main()

