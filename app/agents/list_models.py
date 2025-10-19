import google.generativeai as genai, os
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Listing Gemini models that support generate_content:\n")
for m in genai.list_models():
    if "generateContent" in getattr(m, "supported_generation_methods", []):
        print("•", m.name)
PY
