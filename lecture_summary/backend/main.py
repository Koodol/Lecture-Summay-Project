from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
import os

# 루트의 .env 로드
load_dotenv(find_dotenv())

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(title="Lecture Summary Backend")

# CORS (프론트 로컬 3000 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend is running", "project": os.getenv("GOOGLE_CLOUD_PROJECT")}

# 프론트에서 테스트할 업로드 엔드포인트 (Document AI/Vertex AI는 다음 단계에 연결)
@app.post("/upload")
async def upload_lecture(
    file: UploadFile,
    audience: str = Form(...),   # "novice" | "intermediate"
    purpose: str = Form(...),    # "understanding" | "exam"
):
    # TODO: /tmp 저장 → Document AI 파싱 → Vertex AI 요약/문항 생성
    return {
        "summary": f"[샘플 응답] audience={audience}, purpose={purpose}, file={file.filename}"
    }
