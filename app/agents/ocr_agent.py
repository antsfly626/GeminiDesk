# app/agents/ocr_agent.py
import os
from PIL import Image
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def process_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".mpo"]:
        print(f"[OCR Agent] Using Gemini Vision OCR for image: {file_path}")

        # Convert .mpo to normal RGB JPG ---
        with Image.open(file_path) as img:
            # If it's an MPO, extract the first frame
            if hasattr(img, "n_frames") and img.n_frames > 1:
                img.seek(0)
            img = img.convert("RGB")

            temp_path = file_path + "_converted.jpg"
            img.save(temp_path, "JPEG")
            file_path = temp_path

        # --- Run Gemini OCR ---
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = (
            "You are an OCR and document understanding agent. "
            "Extract all visible text, equations, and diagram captions as Markdown. "
            "Use $$...$$ for math and markdown for layout."
        )
        response = model.generate_content([prompt, Image.open(file_path)])
        return response.text.strip()

    elif ext in [".txt", ".md", ".csv"]:
        print(f"[OCR Agent] Reading text file directly: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        from pdf2image import convert_from_path
        print(f"[OCR Agent] Converting PDF pages to images and processing with Gemini...")
        pages = convert_from_path(file_path)
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        markdown = ""
        for i, page in enumerate(pages):
            response = model.generate_content([
                "Extract all text and diagrams in Markdown format.",
                page
            ])
            markdown += f"\n\n# Page {i+1}\n{response.text.strip()}"
        return markdown.strip()

    else:
        raise ValueError(f"Unsupported file type: {ext}")

if __name__ == "__main__":
    test_dir = r"C:\Users\nehah\GeminiDesk\GeminiDesk\data"
    for file in os.listdir(test_dir):
        file_path = os.path.join(test_dir, file)
        print(f"\n=== Testing: {file} ===")
        try:
            result = process_file(file_path)
            print(result[:400] + ("..." if len(result) > 400 else ""))
        except Exception as e:
            print(f"[OCR Agent] Failed to process {file}: {e}")
