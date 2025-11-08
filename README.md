Perplexity 기반 웹 요약 & 리서치 허브

퍼플렉시티(PPLX) API를 이용해 **웹 페이지 요약**, **위키 검색**, **키워드 맞춤 자료 탐색**을 한 화면에서 제공하는 풀스택 프로젝트입니다. React 프런트엔드는 기본 3분할 레이아웃으로 구성되어 각 기능을 동시에 비교할 수 있습니다.

## 주요 기능
- **URL 요약**: 요청한 페이지를 크롤링해 정제된 본문을 Perplexity로 보내 핵심을 bullet 형태로 요약합니다. Perplexity 호출이 실패하면 로컬 요약으로 자동 대체합니다.
- **Wikipedia 검색 / 강제 탐색**: 모호한 검색어에 대한 후보 제시, 바로가기 링크 제공.
- **키워드 리서치**: 입력 키워드를 기반으로 Perplexity가 신뢰할 만한 참고 자료를 JSON으로 반환하고 UI에서 카드 형태로 시각화합니다.
- **React 멀티 패널 UI**: 세 개의 패널을 기본으로 고정 배치하여 요약/검색/리서치를 동시에 확인합니다.

## 사용 방법 (프런트엔드)
1. **웹 페이지 요약**
   - URL을 입력하면 Perplexity가 요약을 생성합니다. 응답이 실패하면 로컬 요약을 출력하고 사유(`fallbackReason`)를 표시합니다.
2. **Wikipedia 검색**
   - 검색어가 모호하면 상단에 후보 버튼이 나타납니다. 원하는 항목을 누르면 즉시 해당 타이틀로 재조회하여 강제 탐색을 수행합니다.
   - 여전히 모호한 경우 버튼 목록이 다시 갱신되므로, 좁혀 가며 원하는 문서를 찾을 수 있습니다.
3. **키워드 리서치**
   - 여러 키워드를 쉼표로 입력하면 Perplexity가 3~5개의 참고 자료를 JSON으로 반환해 카드로 렌더링합니다.
   - 네트워크 사유로 Perplexity가 응답하지 못하면 Wikipedia/큐레이션 기반 대체 카드가 생성되며, 카드 우측 상단 `perplexity`, `wikipedia`, `curated`, `fallback` 태그로 출처를 구분할 수 있습니다.

기본 레이아웃은 **분할 보기**이며, 각 패널은 동일한 너비로 배치되어 한 화면에서 비교가 가능합니다.

## 폴더 구조
```
project/
├── backend/              # Flask + service layer
├── frontend/             # Vite + React UI
├── requirements.txt
├── .env.example
└── README.md
```

## 환경 변수
`.env.example`을 복사해 `.env`를 만든 뒤 값을 채워주세요.

| 변수 | 설명 |
| --- | --- |
| `PERPLEXITY_API_KEY` | Perplexity에서 발급받은 API 키 |
| `PERPLEXITY_MODEL` | 기본 `llama-3.1-sonar-small-128k-chat` |
| `PERPLEXITY_TEMPERATURE` | 응답 다양성 제어 (기본 0.2) |
| `BACKEND_PORT` | Flask 서버 포트 (기본 8000) |

## 백엔드 실행
```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 값 수정
python run_backend.py  # 또는 python -m backend.app
```

### 주요 API
| Method & Path | 설명 |
| --- | --- |
| `POST /api/summarize-url` | `{ "url": "https://..." }` → 요약, 인용, Perplexity 호출 상태 |
| `GET /api/wiki/search?term=...&lang=ko` | 위키 개요 + 모호성 처리 |
| `GET /api/wiki/force?term=...` | 검색 실패 시 강제 탐색 |
| `POST /api/resources/search` | `{ "keywords": "ai, security" }` → 관련 자료 목록 (Perplexity 실패 시 Wikipedia/큐레이션 자료 자동 제공) |

## 프런트엔드 실행 (Vite + React)
```bash
cd project/frontend
npm install
npm run dev -- --host
```
- 개발 서버 기본 주소: <http://localhost:5173>
- API 기본 주소는 `.env` 없이 `http://localhost:8000`으로 가정합니다. 다른 주소를 쓰려면 `VITE_API_BASE_URL` 환경 변수를 추가하세요.
- Node 18+ 환경을 권장합니다. LTS 이하 버전에서는 `@vitejs/plugin-react`가 설치되지 않습니다.

## 배포 아이디어
1. `npm run build`로 정적 파일을 만들고 Flask에서 서빙하거나, Nginx 등 정적 서버에 업로드합니다.
2. Flask는 `gunicorn` 혹은 `uvicorn` + `hypercorn` 등 WSGI 서버에 올리고 `.env`로 키를 주입합니다.

## 트러블슈팅
- `Perplexity 호출이 실패했습니다` 문구가 반복되면
  1. `.env`의 `PERPLEXITY_API_KEY`가 올바른지 확인하고,
  2. `curl https://api.perplexity.ai/` 등으로 서버에서 직접 접속 가능한지 점검하세요.
  3. API 오류 본문은 UI의 `fallbackReason`에서 바로 확인할 수 있습니다.
- 키워드 리서치에서 `perplexity` 태그가 보이지 않는다면 Perplexity API 접근에 실패한 상태입니다. 대신 `wikipedia` 혹은 `curated` 태그가 표시되며, 이는 대체 데이터가 제공되고 있음을 의미합니다.

## 기대 효과
- URL 핵심 내용을 자동으로 정리해 빠르게 파악
- 위키·자료 탐색 동선 단축
- GitHub/Flask/React 전체 흐름 경험 및 배포 자동화 학습
