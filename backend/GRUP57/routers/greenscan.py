import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Annotated

from models import ProductScan
from database import SessionLocal

# Ortam değişkenlerini yükle
load_dotenv()

# Ortam değişkenleri
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-1.5-flash"
SECRET = os.getenv("SECRET_KEY") or "defaultsecret"
ALGO = os.getenv("ALGORITHM") or "HS256"

if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API anahtarı eksik! Lütfen .env dosyasını kontrol et.")

genai.configure(api_key=GEMINI_API_KEY)

router = APIRouter(prefix="/greenlens", tags=["GreenLens"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User dependency
async def get_current_user(authorization: Annotated[str, Header(...)]):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        user_id = payload.get("id")
        username = payload.get("sub")
        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="Geçersiz token içeriği")
        return {"id": user_id, "username": username}
    except (JWTError, IndexError) as e:
        raise HTTPException(status_code=401, detail=f"Geçersiz veya eksik token: {str(e)}")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# Pydantic giriş modeli
class ScanIn(BaseModel):
    barcode: str | None = None
    product_name: str | None = None

# Barkod veya ürün tarama endpoint
@router.post("/scan")
async def scan(
    data: ScanIn,
    user: user_dependency,
    db: db_dependency
):
    if not data.barcode and not data.product_name:
        raise HTTPException(status_code=400, detail=" barcod veya product_name zorunlu")

    # Gemini’dan sürdürülebilirlik raporu iste
    prompt = (
        f"Ürün: {data.barcode or data.product_name}\n"
        "PFAS, palm yağı, karbon ayak izi ve diğer çevresel riskleri "
        "kısa maddeler halinde özetle. Ardından kullanıcının "
        "daha sürdürülebilir alternatifler için 3 öneri ver."
    )
    gemini = genai.GenerativeModel(GEMINI_MODEL)
    response = gemini.generate_content(prompt)
    report = response.text if hasattr(response, 'text') else str(response)

    # DB’ye kaydet
    scan = ProductScan(
        barcode=data.barcode,
        product_name=data.product_name,
        gemini_report=report,
        owner_id=user["id"]
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return {"scan_id": scan.id, "report": report}

# Kullanıcının geçmiş tarama geçmişi
@router.get("/history")
def history(
    user: user_dependency,
    db: db_dependency
):
    scans = db.query(ProductScan).filter(
        ProductScan.owner_id == user["id"]
    ).order_by(ProductScan.created_at.desc()).all()
    return scans
