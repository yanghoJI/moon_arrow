# 살곶이 삭회 대회 안내 페이지

"살곶이 삭회 대회" 실시간 대시보드입니다. FastAPI 서버가 Google Sheets 데이터를 가져와 캐시하고, 브라우저는 서버에서 렌더링된 HTML을 표시합니다.

## 프로젝트 구조

```
moon_arrow/
├── main.py              # FastAPI 앱, 라우터, 캐시
├── requirements.txt
├── services/
│   └── sheets.py        # Google Sheets fetch, 파싱, 정렬, 팀 구성 로직
├── static/
│   └── styles.css       # 공통 CSS
└── templates/
    ├── base.html         # 공통 레이아웃
    ├── index.html        # 메인 페이지
    ├── rank.html         # 현재 등수
    ├── board.html        # 공지 / 상황판
    ├── squad.html        # 작대 구성
    ├── team.html         # 단체팀 구성
    └── refresh.html      # 갱신 결과
```

## 실행 방법

```bash
pip install -r requirements.txt
python main.py
# → http://0.0.0.0:10555
```

## 페이지

| URL | 설명 |
|-----|------|
| `/` | 메인 안내 페이지 |
| `/rank` | 현재 등수 (총합 → 라운드 합 → 시간별 점수 순 정렬) |
| `/board` | 공지 / 상황판 |
| `/squad` | 작대별 구성원 |
| `/team` | 단체팀 구성 결과 |

## 관리자 API

| URL | 설명 |
|-----|------|
| `/api/refresh` | Google Sheets 전체 갱신 후 변경사항 표시 |
| `/api/team?n=팀수` | 개인전 결과 기반 스네이크 드래프트로 팀 생성 |
| `/api/team/clear` | 팀 구성 초기화 |
| `/api/sheets?url=공유주소` | Google Sheets 공유 주소 저장 후 데이터 갱신 |

### 데이터 갱신 흐름

```
GET /api/refresh
  → Google Sheets 2개 시트 동시 fetch
  → rankings / squads / notices 캐시 업데이트
  → 변경사항 목록 표시
```

### 팀 구성 흐름

```
GET /api/team?n=4
  → 캐시된 rankings 기반 스네이크 드래프트
  → 4팀으로 균등 배분 (팀 합계 최대한 동일하게)
  → /team 으로 리다이렉트
```

## 기술 스택

- **FastAPI** + **Jinja2**: 서버사이드 렌더링
- **httpx**: 비동기 Google Sheets CSV fetch
- **asyncio.gather**: 여러 시트 동시 fetch

## 데이터 소스

Google Sheets 공유 주소는 `/admin` 운영자 페이지에서 저장할 수 있습니다. 저장값은 로컬 `sheet_config.json`에 보관되며, 서버 재시작 후에도 유지됩니다.

시트 탭 이름:
- 등수/작대: `rank`
- 공지: `board`

> 시트 수정 후 반영까지 Google CDN 딜레이가 있을 수 있습니다. `/api/refresh` 호출 후 변경사항이 없으면 잠시 후 재시도하세요.
