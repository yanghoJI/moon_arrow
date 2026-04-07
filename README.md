# 살곶이 삭회 대회 안내 페이지

이 프로젝트는 "살곶이 삭회 대회"의 안내 웹사이트입니다. 참가자들이 대회 정보를 확인하고, 실시간 등수 및 공지사항을 볼 수 있도록 구성되어 있습니다.

## 프로젝트 구조

- `index.html`: 메인 안내 페이지. 대회 제목과 함께 등수 보기 및 공지사항 페이지로 이동하는 버튼을 제공합니다.
- `rank.html`: 현재 등수 표시 페이지. Google Sheets에서 CSV 데이터를 가져와 실시간으로 등수를 테이블 형식으로 표시합니다. 10초마다 자동 갱신됩니다.
- `board.html`: 공지 / 상황판 페이지. Google Sheets에서 CSV 데이터를 가져와 공지사항을 리스트 형식으로 표시합니다. 10초마다 자동 갱신됩니다.
- `squad.html`: 작대 구성 페이지. Google Sheets에서 CSV 데이터를 가져와 작대 번호별로 구성원을 그룹화하여 표시합니다. 10초마다 자동 갱신됩니다.

## 기능

- **메인 페이지**: 대회 안내 및 네비게이션.
- **등수 페이지**: 참가자들의 순위, 총합 점수, 라운드별 합계를 표시. 등수 정렬 로직 포함 (총합 → 라운드 합 → 세부 점수).
- **공지 페이지**: 대회 관련 공지사항을 시간순으로 표시. 공개 여부에 따라 필터링.
- **작대 구성 페이지**: 작대 번호별로 구성원을 나열하여 표시.

## 데이터 소스

모든 동적 데이터는 Google Sheets의 공개 CSV 링크에서 가져옵니다:
- 등수 데이터: `https://docs.google.com/spreadsheets/d/e/2PACX-1vTqsmOlxzgGxrh91wGE0b92x3x40Ta1ZT2l0yd6rTKq5HsrZSng3qocNXwmypouA5F6H68HV46GPVHJ/pub?gid=0&single=true&output=csv`
- 공지 데이터: `https://docs.google.com/spreadsheets/d/e/2PACX-1vTqsmOlxzgGxrh91wGE0b92x3x40Ta1ZT2l0yd6rTKq5HsrZSng3qocNXwmypouA5F6H68HV46GPVHJ/pub?gid=651255673&single=true&output=csv`

Google Sheets의 공유 설정을 통해 데이터를 공개해야 합니다.

## 실행 방법

이 프로젝트는 정적 HTML 파일로 구성되어 있어 별도의 서버가 필요하지 않습니다.

1. 리포지토리를 클론하거나 다운로드합니다.
2. 브라우저에서 `index.html` 파일을 엽니다.
3. 버튼을 클릭하여 등수 또는 공지 페이지로 이동합니다.

## 배포

이 프로젝트는 Git을 통해 배포됩니다. 예를 들어, GitHub Pages를 사용하여 호스팅할 수 있습니다.

1. GitHub 리포지토리에 코드를 푸시합니다.
2. 리포지토리 설정에서 Pages를 활성화하고, 브랜치(예: main)를 선택합니다.
3. 배포된 URL에서 웹사이트를 확인할 수 있습니다.

## 기술 스택

- **HTML**: 페이지 구조.
- **CSS**: 스타일링 (반응형 디자인).
- **JavaScript**: 데이터 가져오기 및 동적 렌더링 (Fetch API 사용).

## 브라우저 지원

모던 브라우저(Chrome, Firefox, Safari 등)에서 지원됩니다. Fetch API를 사용하므로, 오래된 브라우저에서는 작동하지 않을 수 있습니다.

## 라이선스

이 프로젝트는 라이선스 없이 제공됩니다. 자유롭게 사용 및 수정 가능합니다.

## 기여

버그 리포트나 개선 제안은 이슈를 통해 환영합니다.</content>
<parameter name="filePath">/Users/yangho/project/moon_arrow/README.md