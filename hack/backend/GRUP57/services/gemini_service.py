import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Gemini API anahtarını al
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API anahtarı eksik! Lütfen .env dosyasını kontrol et.")

# Gemini yapılandırması
genai.configure(api_key=GEMINI_API_KEY)

def generate_crisis_scenarios(crisis: str) -> dict:
    prompt = (
        f"Act as a sustainability futurist. For the crisis '{crisis}' "
        "generate concise but vivid stories for the years 2030, 2050 and 2100. "
        "Return JSON with keys 2030, 2050, 2100. Write the answer in Turkish."
    )
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    response = model.generate_content(prompt).text

    try:
        # JSON parçasını metinden ayıkla
        json_text = re.search(r"\{.*\}", response, re.S).group()
        return json.loads(json_text)
    except Exception as e:
        raise ValueError(f"JSON ayrıştırma hatası: {e}\nYanıt metni: {response}")