# -*- coding: utf-8 -*-
"""네이버 블로그용 1:1 카드뉴스/인포그래픽 이미지 자동 생성기 (Pillow 기반)"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("output/4772009430")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 윈도우 한글 폰트 탐색
FONT_PATH = "C:/Windows/Fonts/malgunbd.ttf"  # 맑은 고딕 볼드
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

def create_infographic_card():
    # 1080 x 1080 고해상도 정사각형 카드뉴스
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), "#FAFAFA")
    draw = ImageDraw.Draw(img)

    # 폰트 로드
    title_font = ImageFont.truetype(FONT_PATH, 54)
    sub_font = ImageFont.truetype(FONT_PATH, 32)
    card_title_font = ImageFont.truetype(FONT_PATH, 36)
    card_desc_font = ImageFont.truetype(FONT_PATH, 28)
    badge_font = ImageFont.truetype(FONT_PATH, 24)

    # 1. 상단 타이틀 영역 (깔끔한 네이비/버건디 테마)
    draw.rectangle([(0, 0), (W, 200)], fill="#1E293B")
    draw.text((60, 50), "훈훈수산 한입 양념게장", font=sub_font, fill="#94A3B8")
    draw.text((60, 100), "1점 후기 팩트체크 & 실전 팁 3", font=title_font, fill="#FFFFFF")

    # 2. 3대 체크포인트 카드 그리기
    items = [
        {
            "num": "POINT 01",
            "title": "껍질이 너무 딱딱하다? (치아 주의)",
            "desc": "수입산 절단 꽃게 특성상 집게다리는 껍질이 매우 억셉니다.\n몸통 살만 베어 물고, 집게다리는 '찌개 육수용'으로 분리하세요!",
            "badge": "치아 보호 팁",
            "color": "#EF4444"
        },
        {
            "num": "POINT 02",
            "title": "비린내 & 수돗물 냄새 난다? (해동 실수)",
            "desc": "상온 방치나 전자레인지 급속 해동 시 육즙이 빠져 비려집니다.\n택배 수령 즉시 '냉장실에서 반나절 저온 자연해동'이 필수입니다.",
            "badge": "해동의 법칙",
            "color": "#3B82F6"
        },
        {
            "num": "POINT 03",
            "title": "게살 적고 양념 무게만 나간다? (활용법)",
            "desc": "몸통 10~12쪽 내외로 살은 알차게 찹니다. 남은 양념장은\n'따뜻한 밥 + 반숙 후라이 + 참기름 + 김가루' 비빔밥으로 극대화!",
            "badge": "꿀조합 공식",
            "color": "#10B981"
        }
    ]

    card_y = 240
    card_h = 240
    card_w = W - 120  # 960

    for item in items:
        # 카드 배경 그림자 느낌
        draw.rounded_rectangle([(60, card_y), (60 + card_w, card_y + card_h)], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=2)
        
        # 포인트 뱃지
        draw.rounded_rectangle([(90, card_y + 30), (220, card_y + 65)], radius=6, fill=item["color"])
        draw.text((105, card_y + 34), item["badge"], font=badge_font, fill="#FFFFFF")
        
        # 카드 제목
        draw.text((240, card_y + 30), item["title"], font=card_title_font, fill="#0F172A")
        
        # 카드 설명 (2줄)
        draw.text((90, card_y + 95), item["desc"], font=card_desc_font, fill="#475569", spacing=12)
        
        card_y += 265

    # 3. 하단 푸터 영역
    draw.line([(60, H - 70), (W - 60, H - 70)], fill="#CBD5E1", width=1)
    draw.text((60, H - 55), "네이버 블로그 팩트체크 리뷰 | ai-bloger 자동 분석 리포트", font=badge_font, fill="#64748B")

    out_path = OUT_DIR / "infographic_card.png"
    img.save(out_path, quality=95)
    print(f"[OK] 카드뉴스 인포그래픽 생성 완료: {out_path}")
    return out_path

if __name__ == "__main__":
    create_infographic_card()

