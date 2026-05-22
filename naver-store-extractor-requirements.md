# 네이버 스마트스토어 상품 정보 추출기 — 요건 정의서

> Claude Code에 전달하기 위한 요건서. 본 도구는 블로그 포스팅 워크플로우의 전처리 단계로, 상품 정보 추출만 담당한다. 블로그 글 작성은 별도 워크플로우에서 본 도구의 출력을 입력으로 받아 처리한다.

---

## 1. 목적

네이버 스마트스토어 상품 URL을 입력받아, 블로그 포스팅 작성에 필요한 상품 정보를 구조화된 형태로 추출한다. 결과물은 마크다운/JSON으로 저장되어 별도 블로그 초안 작성 워크플로우의 입력으로 사용된다.

## 2. 범위

- **입력**: 네이버 스마트스토어 상품 URL (단일 또는 다수)
- **출력**: 구조화된 상품 정보 파일 (JSON + Markdown + 스크린샷)
- **제외**: 블로그 글 작성 자체는 본 도구의 책임이 아님

---

## 3. 기능 요건

### F1. URL 입력 처리

- CLI 인자 또는 텍스트 파일로 URL 리스트 입력
- 스마트스토어 URL 형식 검증 (`smartstore.naver.com`, `brand.naver.com` 등)
- 잘못된 URL은 스킵하고 로그에 기록

### F2. 페이지 데이터 수집

- Headless 브라우저로 페이지 로드 (JS 렌더링 완료까지 대기)
- 다음 데이터 수집:
  - **HTML 메타데이터**
    - 상품명
    - 가격 (할인가/정가)
    - 브랜드/판매자명
    - 카테고리
    - 평점/리뷰 수
    - 대표 이미지 URL
    - Open Graph 태그, JSON-LD 구조화 데이터
  - **상세 페이지 영역 스크린샷** (이미지 텍스트 추출용)
    - 상품 상세설명 영역만 캡처 (전체 페이지 X)
    - 긴 페이지는 분할 캡처

### F3. 이미지 내 텍스트 추출

- F2에서 캡처한 상세설명 스크린샷을 Claude Vision API에 전달
- 추출 항목:
  - 상품 주요 특징
  - 성분/원재료
  - 효능/효과 (해당되는 카테고리만)
  - 용량/규격
  - 사용법/섭취법
  - 보관법
  - 주의사항
- 카테고리별로 추출 항목이 달라짐 (예: 건강기능식품 vs 식품 vs 가전)

### F4. 결과 저장

- 상품별로 디렉토리 생성: `output/{상품ID 또는 슬러그}/`
- 저장 파일:
  - `product.json`: 구조화 데이터
  - `product.md`: 마크다운 요약 (블로그 작성용 컨텍스트)
  - `screenshot.png`: 상세 스크린샷 원본 (검증용)

### F5. 에러 처리 및 로깅

- 페이지 로드 실패, OCR 실패, 차단 감지 등 케이스별 로그 분리
- 실패 URL은 별도 파일에 누적 (`failed_urls.txt`)
- 재시도 옵션 제공 (지수 백오프)

---

## 4. 비기능 요건

### N1. 성능

- 상품 1개당 처리 시간 30초 이내 목표
- 다수 처리 시 순차 처리 (병렬 X — 차단 회피)

### N2. 차단 회피

- User-Agent 로테이션
- 요청 간 랜덤 딜레이 (3~10초)
- Playwright stealth 모드 권장
- 차단 감지 시 즉시 중단 및 알림

### N3. 비용 관리

- Vision LLM 호출 횟수 = 상품 수 × 분할 스크린샷 수
- 호출 전 캐시 확인 (동일 URL 재처리 방지)
- 추정 비용 로그 출력

### N4. 설정 분리

- `.env`로 시크릿 관리 (API 키)
- `config.yaml`로 추출 항목/카테고리별 프롬프트 관리

---

## 5. 기술 스택 (제안)

- **언어**: Python 3.11+
- **브라우저 자동화**: Playwright (`playwright-python`)
- **Vision LLM**: Anthropic Claude API (`anthropic` SDK)
- **HTML 파싱**: BeautifulSoup4 (메타데이터 추출용)
- **검증**: Pydantic (스키마 정의)
- **CLI**: Typer 또는 argparse

---

## 6. 출력 데이터 스키마 (Pydantic 기준)

```python
class Price(BaseModel):
    original: int | None
    sale: int | None
    currency: str = "KRW"

class ProductDetails(BaseModel):
    features: list[str] = []
    ingredients: list[str] | None = None
    effects: list[str] | None = None
    specs: dict[str, str] = {}
    usage: str | None = None
    storage: str | None = None
    caution: str | None = None

class Product(BaseModel):
    url: str
    product_id: str
    name: str
    brand: str | None
    category: str | None
    price: Price
    rating: float | None
    review_count: int | None
    main_image_url: str
    details: ProductDetails
    extracted_at: datetime
    source_screenshots: list[str]  # 파일 경로
```

---

## 7. 디렉토리 구조 (제안)

```
naver-store-extractor/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI 엔트리
│   ├── fetcher.py           # Playwright 페이지 수집
│   ├── parser.py            # HTML 메타데이터 파싱
│   ├── vision.py            # Claude Vision 호출
│   ├── schemas.py           # Pydantic 모델
│   └── config.py            # 설정 로드
├── config/
│   ├── prompts.yaml         # 카테고리별 추출 프롬프트
│   └── selectors.yaml       # CSS 선택자 모음
├── output/                  # 결과 저장
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. 단계별 구현 우선순위

| 단계 | 범위 | 검증 기준 |
|---|---|---|
| **MVP (1차)** | 단일 URL → 메타데이터 + Vision 추출 → JSON 저장 | 샘플 상품 1개에서 상품명/가격/상세 텍스트 추출 성공 |
| **2차** | 다수 URL 처리 + 캐시 + 에러 핸들링 | 5개 URL 일괄 처리, 중복 호출 방지 동작 |
| **3차** | 카테고리별 프롬프트 분기 + 마크다운 출력 포맷팅 | 건강식품/식품/가전 각 1개씩 카테고리별 정확도 차이 확인 |
| **4차** | 차단 회피 강화, 재시도 로직, CLI UX | 30개 연속 처리 시 차단 없이 완료 |

---

## 9. 검증 기준

- 건강기능식품 1개, 식품 1개, 가전 1개 — 세 카테고리 샘플 상품으로 추출 결과의 정확도를 사람이 직접 확인
- 추출된 정보가 실제 상품 페이지와 일치하는지 spot-check
- 동일 URL 재실행 시 캐시 적중으로 Vision API 미호출 확인

---

## 10. Claude Code 작업 지시 시 추가 컨텍스트

요건서와 함께 다음을 명시해 전달:

- 운영 환경: (예: macOS / Ubuntu)
- Python 버전: 3.11+ 고정
- Anthropic API 키: `.env`에 `ANTHROPIC_API_KEY`로 주입됨
- 우선 MVP만 구현 (2차 이후는 동작 확인 후 별도 요청)
- 테스트용 샘플 URL: (실제 URL 1~2개 첨부)
- 출력 디렉토리 위치 및 파일명 규칙 준수
- 비밀번호/API 키 평문 출력 금지

---

## 11. 주의사항

- 본 도구는 본인이 어필리에이트 활동 중인 상품의 정보 정리 목적으로 사용한다
- 네이버 스마트스토어 robots.txt 및 이용약관을 검토하여 위반 소지를 사전에 확인할 것
- 대량 자동 수집은 IP 차단 사유가 될 수 있으므로 요청 간격을 충분히 두어야 한다
