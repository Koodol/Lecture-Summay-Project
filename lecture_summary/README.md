기본적인 프론트 백 틀을 만듬, 추가로 클라우드에서 api키 생성해서 연동함 연동하는 json은 공유하면 안되서 일단빼놓음

backend 패키지 설치
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv `
  google-cloud-aiplatform google-cloud-documentai google-cloud-storage google-cloud-firestore

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
