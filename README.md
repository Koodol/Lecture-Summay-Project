# Lecture Summary Project

이 프로젝트는 강의 자료(PDF/PPT)를 업로드하면 Google Cloud Document AI로 텍스트를 추출하고, Vertex AI Gemini를 이용해 다음 3가지를 자동 생성합니다.

- 요약: 핵심 요약과 섹션별 불릿
- 용어 정리: term/definition/importance 리스트
- 연습 문제: MCQ/Short 총 10문항

## 아키텍처 개요

- Backend: FastAPI, Document AI, Vertex AI, Google Cloud Storage(GCS)
- Frontend: React (파일 업로드 UI, 결과 표시)

## 처리 흐름(Backend)

1. 업로드 파일 임시 저장
2. Document AI로 텍스트 추출
   - 온라인 처리 사용, 이미지/도표 텍스트 포함 모드(non‑imageless)
   - 페이지 한도를 지키기 위해 15페이지 단위로 분할 처리 후 결과 병합
3. 원본 파일을 GCS에 업로드하여 `gs://...` URI 생성
   - 전파/캐시 이슈를 줄이기 위해 업로드 파일명에 타임스탬프 접두어 부여
4. Vertex AI Gemini 파이프라인 실행 (텍스트 + 원본 파일 URI 동시 제공)
   - 요약 → 용어 → 문제 순으로 별도 호출
   - JSON 강제 + 간소화 프롬프트 재시도 + 규칙 기반 폴백으로 항상 비지 않는 결과를 보장

## API

- POST `/upload`
  - form-data
    - `file`: PDF/PPT 파일
    - `audience`: `novice` | `intermediate`
    - `purpose`: `understanding` | `exam`
  - response(JSON)
    - `meta`: { `pageCount`, `lowTextPages`, `tablesTotal` }
    - `summary`: { `high_level`: string, `sections`: [{ `title`, `bullets`: string[] }] }
    - `glossary`: [{ `term`, `definition`, `importance` }]
    - `terms`: glossary 별칭(alias)
    - `questions`: 10개 [{ `type`, `stem`, `choices?`, `answer`, `rationale`, `difficulty` }]
    - `counts`: { `terms`, `questions`, `summarySections` }

## 환경 변수(.env)

- 공통
  - `GOOGLE_CLOUD_PROJECT`
  - `GOOGLE_APPLICATION_CREDENTIALS` (서비스 계정 키 경로)
  - `ALLOWED_ORIGINS` (예: `http://localhost:3000`)
- Document AI
  - `DOC_AI_LOCATION` (예: `us`)
  - `DOC_AI_PROCESSOR_ID`
  - `DOC_AI_GCS_BUCKET`, `DOC_AI_GCS_PREFIX` (예: `docai`)
  - `LIBREOFFICE_PATH` (PPT→PDF 변환 필요 시, Windows 경로)
- Vertex AI
  - `VERTEX_LOCATION` (예: `us-central1`)
  - `VERTEX_MODEL` (예: `gemini-2.5-pro` — 프로젝트/리전에 가용한 모델명 사용)

## 권한/설정

- Vertex 실행 주체(서비스 에이전트/서비스 계정)에 대상 GCS 버킷에 대한 `roles/storage.objectViewer` 권한 필요
- Document AI Processor ID는 콘솔에서 생성 및 활성화 필요

## 실행 방법

- Backend
  - `cd backend`
  - `pip install -r requirements.txt` (또는 README 하단 패키지 목록 참고)
  - `uvicorn main:app --reload --port 8080`
- Frontend
  - `cd frontend`
  - `npm start`

## 동작 특성 및 안정화 포인트

- 30p 초과 문서도 15p 단위로 분할 처리하여 온라인 API 한도 초과 에러를 회피합니다.
- GCS 업로드 시 파일명에 타임스탬프를 붙여 최신 파일을 안정적으로 참조합니다.
- LLM 응답은 JSON만 허용하며, 실패 시 간소화 프롬프트 재시도 후 규칙 기반 폴백으로 항상 결과를 반환합니다.

## 문제 해결(Troubleshooting)

- 400 PAGE_LIMIT_EXCEEDED: 분할 처리(15p) 로직이 포함되어 있어 재현되지 않아야 합니다. 그래도 발생하면 분할 청크/imageless 설정 확인.
- 결과가 비어 보임: 응답의 `counts` 값을 확인하세요. 0이면 권한(GCS 접근), 모델 가용성, 입력 텍스트 품질을 점검.
- 무작위성: 필요 시 temperature를 더 낮춰 일관성을 높일 수 있습니다.

---
## Note
기본적인 프론트 백 틀을 만듬, 추가로 클라우드에서 api키 생성해서 연동함 연동하는 json은 공유하면 안되서 일단빼놓음

backend 패키지 설치
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv `
  google-cloud-aiplatform google-cloud-documentai google-cloud-storage google-cloud-firestore pypdf

.env와 키.json은 공개하면안됨으로 깃할때는 제외

백엔드 실행(가상환경이 켜져있어야함 : .venv\Scripts\Activate.ps1)
cd backend
python -m uvicorn main:app --reload --port 8080

루트용
cd "C:\Users\user\OneDrive\바탕 화면\Project\lecture_summary"
python -m uvicorn main:app --reload --port 8080 --app-dir backend

프론트 실행
cd frontend
npm start