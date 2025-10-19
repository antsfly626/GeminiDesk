# app/agents/ocr_agent.py
import os
from PIL import Image
import google.generativeai as genai
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent  # folder of current file
DATA_DIR = BASE_DIR.parent.parent /"data"

print(DATA_DIR)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# DATA_DIR = r"/data/events"

def extract_text(file_path: str) -> str:
    """Extract text or OCR content from any file using Gemini."""
    ext = os.path.splitext(file_path)[1].lower()
    fname = os.path.basename(file_path)
    print(f"[Gemini OCR] Processing: {fname}")

    model = genai.GenerativeModel("models/gemini-2.5-flash")

    # Handle text directly
    if ext in [".txt", ".md", ".csv"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    # Handle images
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        prompt = (
            "Extract all visible text, labels, equations, and diagram captions "
            "from this image as Markdown. Use $$...$$ for math and Markdown formatting."
        )

        # ✅ Force-clean the image buffer (prevents pip install google-generativeaiMPO issue)
        with Image.open(file_path) as img:
            if hasattr(img, "n_frames") and img.n_frames > 1:
                img.seek(0)
            img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": buffer.read()}]
        )
        return response.text.strip()

    # Handle PDFs
    elif ext == ".pdf":
        from pdf2image import convert_from_path
        print(f"[Gemini OCR] Converting PDF to images...")
        pages = convert_from_path(file_path)
        text = ""
        for i, page in enumerate(pages):
            buf = BytesIO()
            page.save(buf, format="JPEG")
            buf.seek(0)
            response = model.generate_content([
                f"Extract all text and diagrams from page {i+1} as Markdown.",
                {"mime_type": "image/jpeg", "data": buf.read()}
            ])
            text += f"\n\n# Page {i+1}\n{response.text.strip()}"
        return text.strip()

    else:
        print(f"[Gemini OCR] Unsupported file type: {ext}")
        return ""

if __name__ == "__main__":
    for file in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, file)
        if not os.path.isfile(file_path):
            continue
        try:
            text = extract_text(file_path)
            if text:
                print(f"\n--- Extracted from {file} ---\n{text[:500]}...\n")
        except Exception as e:
            print(f"[Gemini OCR] Error on {file}: {e}")
