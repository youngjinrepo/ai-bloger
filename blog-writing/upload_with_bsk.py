# -*- coding: utf-8 -*-
"""네이버 블로그 bsk 자동 업로더

사용법:
  python blog-writing/upload_with_bsk.py <마크다운파일경로>
"""
import re
import subprocess
import sys
import time
import base64
import json
import win32clipboard
from pathlib import Path

def markdown_to_naver_html(md_text: str) -> dict:
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

    body_match = re.search(r"## 본문\s*\n(.*?)(?:\(공백 포함|## 사진|\Z)", md_text, re.DOTALL)
    raw_body = body_match.group(1).strip() if body_match else md_text

    tags = []
    tag_match = re.search(r"## .*?태그.*?\n(.*?)(?:\Z|##)", md_text, re.DOTALL)
    if tag_match:
        tags = re.findall(r"#([\w가-힣]+)", tag_match.group(1))

    html_lines = []
    chunks = raw_body.split("\n\n")

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or chunk.startswith("---"):
            continue

        if chunk.startswith("###"):
            sub = re.sub(r"^###\s*", "", chunk).strip()
            html_lines.append(f'<p style="font-size: 19px; font-weight: bold; color: #111; margin-top: 28px; margin-bottom: 12px; line-height: 1.4;">■ {sub}</p>')
        elif chunk.startswith("##"):
            sub = re.sub(r"^##\s*", "", chunk).strip()
            html_lines.append(f'<p style="font-size: 21px; font-weight: bold; color: #000; margin-top: 32px; margin-bottom: 14px; line-height: 1.4;">{sub}</p>')
        else:
            p_text = chunk
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", p_text)
            p_text = p_text.replace("\n", "<br>")
            html_lines.append(f'<p style="font-size: 16px; color: #333; line-height: 1.8; margin-bottom: 14px;">{p_text}</p>')

    return {
        "title": title,
        "html": "".join(html_lines),
        "tags": " ".join([f"#{t}" for t in tags]),
    }

def run_bsk(cmd_args, session=None):
    bsk_path = r"C:\Users\Guest1\.local\bin\bsk.exe"
    full_args = [bsk_path] + cmd_args
    if session:
        full_args.extend(["--session", session])
    result = subprocess.run(full_args, capture_output=True, text=True, encoding='utf-8')
    return result

def get_or_create_session():
    res = run_bsk(["session", "list", "--json"])
    if res.returncode == 0:
        sessions = json.loads(res.stdout)
        if sessions:
            return sessions[0]["session_id"]
    
    print("활성 세션이 없어 새로 생성합니다...")
    res = run_bsk(["session", "start", "--json"])
    if res.returncode == 0:
        data = json.loads(res.stdout)
        return data["session_id"]
    
    print("세션 생성 실패:", res.stderr)
    sys.exit(1)

def evaluate_js(js_code, session):
    safe_js = js_code.replace('"', '\\"').replace('\n', ' ')
    return run_bsk(["evaluate", f'"{safe_js}"'], session)

def set_clipboard(content: str, is_html=False):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    try:
        if is_html:
            html = f"Version:0.9\r\nStartHTML:0000000105\r\nEndHTML:0000000000\r\nStartFragment:0000000000\r\nEndFragment:0000000000\r\n<html><body>\r\n<!--StartFragment-->\r\n{content}\r\n<!--EndFragment-->\r\n</body></html>"
            
            # byte 단위 길이 계산을 위한 인코딩
            html_bytes = html.encode('utf-8')
            start_frag = html[:html.find('<!--StartFragment-->') + len('<!--StartFragment-->') + 2].encode('utf-8')
            end_frag = html[:html.find('<!--EndFragment-->')].encode('utf-8')
            
            html = html.replace('EndHTML:0000000000', f'EndHTML:{len(html_bytes):010d}')
            html = html.replace('StartFragment:0000000000', f'StartFragment:{len(start_frag):010d}')
            html = html.replace('EndFragment:0000000000', f'EndFragment:{len(end_frag):010d}')
            
            html_format = win32clipboard.RegisterClipboardFormat('HTML Format')
            win32clipboard.SetClipboardData(html_format, html.encode('utf-8'))
        
        # 텍스트 포맷 (HTML이든 아니든 폴백용으로 세팅)
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, content.encode('utf-16le'))
    finally:
        win32clipboard.CloseClipboard()

def send_paste(session):
    run_bsk(["press", "Control+v"], session)

def main():
    if len(sys.argv) < 2:
        print("사용법: python upload_with_bsk.py <마크다운파일경로>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"파일이 없습니다: {target}")
        sys.exit(1)

    text = target.read_text(encoding="utf-8")
    parsed = markdown_to_naver_html(text)
    
    session = get_or_create_session()
    print(f"세션 ID: {session}")
    
    print("1. 네이버 블로그 글쓰기 페이지로 이동...")
    # 브라우저 행 걸림 방지용 비동기 네비게이션
    evaluate_js("setTimeout(() => window.location.href = 'https://blog.naver.com/GoBlogWrite.naver', 10); 'navigating';", session)
    time.sleep(6)
    
    print("2. 글쓰기 팝업 취소...")
    cancel_js = """
    (function() {
        var doc = document.getElementById('mainFrame').contentWindow.document;
        var btns = Array.from(doc.querySelectorAll('button'));
        var cancelBtn = btns.find(b => b.innerText.trim() === '취소');
        if (cancelBtn) { cancelBtn.click(); return 'clicked'; }
        return 'not_found';
    })();
    """
    for _ in range(5):
        res = evaluate_js(cancel_js, session)
        if "clicked" in res.stdout:
            print("  -> 취소 버튼 클릭 성공")
            break
        time.sleep(1)
    
    time.sleep(1)

    print(f"3. 제목 입력: {parsed['title']}")
    set_clipboard(parsed['title'], is_html=False)
    evaluate_js("var doc = document.getElementById('mainFrame').contentWindow.document; var t = doc.querySelector('.se-documentTitle span.__se-node'); if(t){ t.innerHTML=''; t.focus(); }", session)
    time.sleep(1)
    send_paste(session)
    time.sleep(1)

    print("4. 본문 및 태그(HTML) 붙여넣기...")
    html_with_tags = parsed["html"] + f'<p><br></p><p>{parsed["tags"]}</p>'
    set_clipboard(html_with_tags, is_html=True)
    evaluate_js("var doc = document.getElementById('mainFrame').contentWindow.document; var t = doc.querySelectorAll('.se-text-paragraph span.__se-node')[0]; if(t) t.focus();", session)
    time.sleep(1)
    send_paste(session)
    time.sleep(3)

    print("5. 임시저장(저장) 클릭...")
    save_js = "var doc = document.getElementById('mainFrame').contentWindow.document; var saveBtn = doc.querySelector('button.se-save-button') || Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('저장')); if(saveBtn) saveBtn.click();"
    save_script_b64 = base64.b64encode(save_js.encode('utf-8')).decode('utf-8')
    save_wrapper_js = f"var s = document.createElement('script'); s.innerText = decodeURIComponent(escape(atob('{save_script_b64}'))); document.body.appendChild(s);"
    evaluate_js(save_wrapper_js, session)
    time.sleep(2)
    
    print("\n[SUCCESS] bsk 업로드가 완료되었습니다. 브라우저를 확인하세요.")

if __name__ == "__main__":
    main()
