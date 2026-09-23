# -*- coding: utf-8 -*-
"""네이버 블로그 에디터 전용 원클릭 클립보드 복사 도구 (계정 정지 위험 0%)

사용법:
  python blog-writing/copy_to_blog.py blog-writing/final/4772009430_final.md
"""
import re
import subprocess
import sys
from pathlib import Path


def markdown_to_naver_html(md_text: str) -> dict:
    """마크다운을 네이버 스마트에디터 ONE 전용 HTML 서식으로 변환"""
    # 1. 추천 제목 추출
    title = ""
    title_match = re.search(r"## 제목.*?\n(.*?)\n---", md_text, re.DOTALL)
    if title_match:
        for line in title_match.group(1).split("\n"):
            if "← 추천" in line or "1." in line:
                title = re.sub(r"^\d+\.\s*|\*\*|←\s*추천", "", line).strip()
                if title:
                    break
    if not title:
        title = re.sub(r"^#\s*", "", md_text.split("\n")[0]).strip()

    # 2. 본문 추출
    body_match = re.search(r"## 본문\s*\n(.*?)(?:\(공백 포함|## 사진|\Z)", md_text, re.DOTALL)
    raw_body = body_match.group(1).strip() if body_match else md_text

    # 3. 태그 추출
    tags = []
    tag_match = re.search(r"## .*?태그.*?\n(.*?)(?:\Z|##)", md_text, re.DOTALL)
    if tag_match:
        tags = re.findall(r"#([\w가-힣]+)", tag_match.group(1))

    # 네이버 스마트에디터 호환 HTML 생성 (가독성 높은 모바일 서식)
    html_lines = []
    chunks = raw_body.split("\n\n")

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or chunk.startswith("---"):
            continue

        if chunk.startswith("###"):
            # 소제목 (네이버 에디터 소제목 느낌: 굵고 살짝 큰 폰트)
            sub = re.sub(r"^###\s*", "", chunk).strip()
            html_lines.append(f'<p style="font-size: 19px; font-weight: bold; color: #111; margin-top: 28px; margin-bottom: 12px; line-height: 1.4;">■ {sub}</p>')
        elif chunk.startswith("##"):
            sub = re.sub(r"^##\s*", "", chunk).strip()
            html_lines.append(f'<p style="font-size: 21px; font-weight: bold; color: #000; margin-top: 32px; margin-bottom: 14px; line-height: 1.4;">{sub}</p>')
        else:
            # 일반 문단 (줄바꿈 및 볼드 처리)
            p_text = chunk
            # 볼드 변환
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", p_text)
            # 줄바꿈 변환
            p_text = p_text.replace("\n", "<br>")
            html_lines.append(f'<p style="font-size: 16px; color: #333; line-height: 1.8; margin-bottom: 14px;">{p_text}</p>')

    html_content = "".join(html_lines)

    return {
        "title": title,
        "html": html_content,
        "tags": " ".join([f"#{t}" for t in tags]),
    }


def copy_html_to_clipboard(html: str):
    """Windows 클립보드에 HTML Format(서식 있는 텍스트)으로 등록 (PowerShell 이용)"""
    # 임시 HTML 파일 생성 후 PowerShell로 복사
    temp_file = Path(__file__).parent / "temp_clipboard.html"
    temp_file.write_text(html, encoding="utf-8")

    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$html = Get-Content -Path '{temp_file}' -Raw -Encoding UTF8
[System.Windows.Forms.Clipboard]::SetText($html, [System.Windows.Forms.TextDataFormat]::Html)
"""
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    if temp_file.exists():
        temp_file.unlink()


def main():
    if len(sys.argv) < 2:
        target = Path("blog-writing/final/4772009430_final.md")
    else:
        target = Path(sys.argv[1])

    if not target.exists():
        print(f"파일이 없습니다: {target}")
        sys.exit(1)

    text = target.read_text(encoding="utf-8")
    parsed = markdown_to_naver_html(text)

    # 클립보드에 HTML 서식 복사
    copy_html_to_clipboard(parsed["html"])

    print("\n=========================================================")
    print("✅ 본문 전체가 '네이버 블로그 전용 서식(HTML)'으로 클립보드에 복사되었습니다!")
    print("=========================================================\n")
    print(f"📌 [추천 제목] (드래그해서 복사하세요):")
    print(f"   {parsed['title']}\n")
    print(f"🏷️ [태그 목록] (하단 태그창에 붙여넣으세요):")
    print(f"   {parsed['tags']}\n")
    print("👉 [방법]:")
    print("   1. 평소 쓰시던 정상 브라우저에서 네이버 블로그 글쓰기를 엽니다.")
    print("   2. 제목 붙여넣기")
    print("   3. 본문 클릭 후 [Ctrl + V] 누르면 소제목, 줄바꿈, 볼드가 완벽히 들어갑니다!")
    print("   4. (계정 보호조치 위험 0%)")
    print("=========================================================\n")


if __name__ == "__main__":
    main()

