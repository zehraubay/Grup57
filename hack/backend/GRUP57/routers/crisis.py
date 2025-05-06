# routers/crisis.py
from dotenv import load_dotenv
load_dotenv()
import asyncio, os, openai, google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import SessionLocal
from models   import CrisisSim
from routers.auth import SECRET_KEY, ALGORITHM, get_current_user   # User obj. döner

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not OPENAI_API_KEY or not GEMINI_API_KEY:
    raise RuntimeError("API anahtarları eksik")

openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "models/gemini-1.5-flash"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(
    prefix="/crisis",
    tags=["Crisis"],
    dependencies=[Depends(oauth2_scheme)]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CrisisIn(BaseModel):
    crisis: str

async def gemini_scenario(topic: str) -> str:
    model  = genai.GenerativeModel(GEMINI_MODEL)
    prompt = (
        f"{topic} için 2030, 2050 ve 2100 yıllarına ait, her biri en az 120 kelime "
        f"uzunluğunda, sürdürülebilir gelecek odaklı, bilinçlendirici ayrı senaryolar üret. "
        f"Çıktıyı tam olarak aşağıdaki başlıklarla ver:\n\n"
        f"### 2030\n...\n\n### 2050\n...\n\n### 2100\n..."
    )
    return model.generate_content(prompt).text

def split_year_blocks(text: str) -> dict[str, str]:
    blocks: dict[str,str] = {}
    for section in text.split("### ")[1:]:
        year = section[:4]
        content = section[4:].strip()
        blocks[year] = content
    return blocks

async def gemini_prompt(topic: str, year: str, text: str) -> str:
    model = genai.GenerativeModel(GEMINI_MODEL)
    req   = (
        f"{topic}, {year} senaryosu: {text} — , İngilizce, DALL·E 3’e uygun "
        f"fotoğraf gerçekçiliğinde görsel prompt"
    )
    return model.generate_content(req).text

def first_sentence(s: str) -> str:
    return s.split(".")[0].strip()

async def create_image(prompt: str) -> str:
    resp = await openai_client.images.generate(
        model="dall-e-3",
        prompt=first_sentence(prompt),
        size="1024x1024",
        n=1
    )
    return resp.data[0].url

@router.post("/simulate", response_model=dict)
async def simulate(
    body: CrisisIn,
    user:      Session = Depends(get_current_user),  # User modeli
    db:        Session = Depends(get_db)
):
    full_text = await gemini_scenario(body.crisis)
    parts     = split_year_blocks(full_text)

    prompt_tasks = [gemini_prompt(body.crisis, y, t) for y, t in parts.items()]
    prompts      = await asyncio.gather(*prompt_tasks)

    image_urls   = await asyncio.gather(*[create_image(p) for p in prompts])

    result = {
        year: {"text": parts[year], "image_url": image_urls[idx]}
        for idx, year in enumerate(parts)
    }

    sim = CrisisSim(crisis=body.crisis, scenarios=result, owner_id=user.id)
    db.add(sim); db.commit(); db.refresh(sim)

    return {"sim_id": sim.id, "scenarios": result}