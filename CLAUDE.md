# ai-bloger 프로젝트 지시사항

## 작업 방식

- 블로그 파이프라인(Phase 1→2→3→최종 발행본) 진행 시 중간에 확인 묻지 말고 yes로 자동 진행
- 글자수 부족 시 사용자 확인 없이 바로 보강
- 다음 단계로 넘어갈 때 "진행할까요?", "계속할까요?" 같은 질문 생략
- 상품 URL 받으면 바로 스크래핑 → Phase 1 → Phase 2(5인 초안) → 채점 → 합본 → Phase 3 → 최종 발행본까지 한 번에 진행
- 단계별 완료 후 결과 요약만 출력하고 다음 단계 바로 시작

## 기록 규칙

- 판단이 들어간 작업은 `history/`에 근거와 날짜를 남길 것 (규칙: `history/README.md`)
  - 아이템 발굴 → `discover.py`가 `history/discover/`에 자동 저장
  - 상품 검토 → `history/products/{상품ID}.md`, `_index.md`에 한 줄 추가. **탈락 상품도 반드시 기록**
  - 글 작성 → `history/articles/{상품ID}.md`에 최종 각도 + **버린 각도와 이유** + 문체 피드백
- 글 쓰기 전 `blog-writing/prompts/07_writing_style.md`를 먼저 읽을 것
