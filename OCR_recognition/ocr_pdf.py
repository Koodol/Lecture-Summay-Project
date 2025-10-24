import io
import os

import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# 환경설정
load_dotenv()
GOOGLE_API_KEY = "GOOGLE_API_KEY"

if not GOOGLE_API_KEY:
    raise ValueError("환경변수 GOOGLE_API_KEY가 없습니다. .env에 GOOGLE_API_KEY=... 를 추가하거나 스크립트 내에 직접 설정하세요.")

genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.5-flash-preview-05-20"

generation_config = {
    "temperature": 0.0,
}

print(f"사용 모델: {MODEL_NAME}") 

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
)

def pil_to_png_bytes(img: Image.Image) -> bytes:
    """PIL 이미지를 PNG 형식의 바이트로 변환합니다."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def extract_text_from_pdf(pdf_path: str, dpi: int = 300, pages_per_chunk: int = 8) -> str:
    """
    PDF의 모든 페이지를 이미지로 변환 후 Gemini로 텍스트 추출.
    - pages_per_chunk: 한 번의 요청에 묶을 페이지 수
    """
    doc = None
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"총 {total_pages} 페이지의 PDF 파일을 처리합니다... (모델: {MODEL_NAME})")

        image_parts = []
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            # 고해상도 DPI 설정
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            png_bytes = pil_to_png_bytes(img)
            image_parts.append({
                "mime_type": "image/png",
                "data": png_bytes,
            })
            if (page_num + 1) % 10 == 0 or (page_num + 1) == total_pages:
                 print(f"  {page_num + 1}/{total_pages} 페이지 이미지 변환 완료...")
        print("이미지 변환 완료. Gemini API로 텍스트 추출을 시작합니다...")

        # 배치 처리
        all_texts = []
        for start in range(0, total_pages, pages_per_chunk):
            end = min(start + pages_per_chunk, total_pages)
            batch = image_parts[start:end]
            print(f"  API 호출: 페이지 {start + 1}–{end} 처리 중...")

            # 프롬프트 + 이미지들
            prompt_parts = [
                ("주어진 이미지들은 문서의 연속된 페이지입니다. "
                 "각 이미지에서 보이는 모든 텍스트를 빠짐없이, 원문 그대로, 페이지 순서를 유지하여 추출하세요. "
                 "수정/요약/정규화하지 말고, 원문을 그대로 옮기세요.")
            ]
            prompt_parts.extend(batch)

            try:
                # API 호출
                response = model.generate_content(prompt_parts)
                # response.text 대신 response.parts[0].text 를 확인 (안전성)
                text = ""
                if response.parts:
                    text = response.parts[0].text
                elif hasattr(response, "text"):
                     text = response.text # text 속성이 있는 경우 대비
                
                # 배치 범위 주석(선택)
                header = f"\n\n----- [페이지 {start+1}–{end}] -----\n"
                all_texts.append(header + (text or "[응답 없음]"))

            except Exception as api_error:
                print(f"  [오류] 페이지 {start+1}–{end} 처리 중 API 오류 발생: {api_error}")
                # API 오류 발생 시, 해당 배치를 건너뛰고 다음 배치를 시도
                header = f"\n\n----- [페이지 {start+1}–{end} (오류 발생)] -----\n"
                all_texts.append(header + f"{api_error}\n")
        return "".join(all_texts)

    except Exception as e:
        return f"파일 처리 중 오류가 발생했습니다: {e}"
    finally:
        if doc is not None:
            doc.close()
            print("PDF 파일 리소스를 닫았습니다.")

if __name__ == "__main__":
    pdf_file_path = "path/.pdf"
    
    if not os.path.exists(pdf_file_path):
        print(f"오류: PDF 파일을 찾을 수 없습니다 - {pdf_file_path}")
    else:
        extracted_text = extract_text_from_pdf(pdf_file_path, dpi=300, pages_per_chunk=8)
        
        print("\n--- [ 최종 추출 결과 ] ---\n")
        print(extracted_text)
        
        # 결과를 파일로 저장 (선택 사항)
        output_filename = "extracted_text_test.txt"
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            print(f"\n--- 결과가 '{output_filename}' 파일에 저장되었습니다. ---")
        except Exception as e:
            print(f"\n--- 결과를 파일에 저장하는 중 오류 발생: {e} ---")
