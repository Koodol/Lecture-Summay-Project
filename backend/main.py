from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from google.cloud import storage
from mimetypes import guess_type
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os, tempfile, shutil, time

from services.document_ai import extract_document
from services.vertex_gemini import run_pipeline_hybrid

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# GCS 업로드 유틸
def _upload_raw_to_gcs(local_path: str, bucket: str, prefix: str, dst_name: str) -> str:
    client = storage.Client()
    bkt = client.bucket(bucket)
    blob = bkt.blob(f"{prefix}/raw/{dst_name}")
    blob.upload_from_filename(local_path)
    return f"gs://{bucket}/{prefix}/raw/{dst_name}"

app = FastAPI(title="Lecture Summary Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend OK", "project": os.getenv("GOOGLE_CLOUD_PROJECT")}

@app.post("/upload")
async def upload_lecture(
    file: UploadFile,
    audience: str = Form(...),  # "novice" | "intermediate"
    purpose: str = Form(...),   # "understanding" | "exam"
    mode: str = Form("auto"),  # 선택: auto/gemini_only/docai_then_gemini
):
    DOC_AI_BUCKET = os.getenv("DOC_AI_GCS_BUCKET")
    DOC_AI_PREFIX = os.getenv("DOC_AI_GCS_PREFIX", "docai")

    # 1) 업로드된 파일을 임시 폴더에 저장하고 Document AI로 텍스트 추출
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, file.filename)
        with open(dst, "wb") as f:
            shutil.copyfileobj(file.file, f)

        doc = extract_document(dst)
        full_text = doc.get("full_text", "")

        # 2) 원본 파일을 GCS에 업로드하고 gs://... URI 생성
        stamped_name = f"{int(time.time())}_{file.filename}"
        gcs_uri = _upload_raw_to_gcs(dst, DOC_AI_BUCKET, DOC_AI_PREFIX, stamped_name)
        mime = file.content_type or (guess_type(file.filename)[0] or "application/pdf")

    # 3) 생성 파이프라인 실행: 텍스트 + 원본 파일을 함께 제공
    result = run_pipeline_hybrid(
        full_text=full_text,
        audience=audience,
        purpose=purpose,
        file_uri=gcs_uri,
        mime_type=mime,
    )

    # 평탄화된 응답 구조와 생성 개수(counts) 반환
    return {
        "meta": {
            "pageCount": len(doc.get("pages", [])),
            "lowTextPages": doc.get("low_text_pages", []),
            "tablesTotal": doc.get("tables_total", 0),
        },
        "summary": result.get("summary"),
        "glossary": result.get("glossary"),
        "terms": result.get("glossary"),
        "questions": result.get("questions"),
        "counts": {
            "terms": len(result.get("glossary") or []),
            "questions": len(result.get("questions") or []),
            "summarySections": len((result.get("summary") or {}).get("sections") or []),
        },
    }

