import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Annotated

from database import SessionLocal
from models import ProductScan

# Ortam değişkenleri
SECRET = os.getenv("SECRET_KEY") or "defaultsecret"
ALGO = os.getenv("ALGORITHM") or "HS256"

router = APIRouter(prefix="/product", tags=["Product"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User dependency
async def get_current_user(authorization: str = Depends()):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        user_id = payload.get("id")
        username = payload.get("sub")
        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="❌ Geçersiz token içeriği")
        return {"id": user_id, "username": username}
    except (JWTError, IndexError) as e:
        raise HTTPException(status_code=401, detail=f"❌ Geçersiz veya eksik token: {str(e)}")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# Pydantic giriş modeli
class BarcodeIn(BaseModel):
    barcode: str

# OpenFoodFacts API’den veri çekme
def fetch_product_data(barcode: str) -> dict:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != 1:
        return {"found": False}

    product = data["product"]
    ingredients = product.get("ingredients_text", "").lower()

    return {
        "found": True,
        "barcode": barcode,
        "product_name": product.get("product_name", "Bilinmiyor"),
        "contains_palm": "palm" in ingredients,
        "pfos_risk": any(x in ingredients for x in ["pfas", "ptfe"]),
        "carbon_kg": product.get("carbon-footprint_100g", None)
    }

# FastAPI endpoint
@router.post("/scan-barcode")
def scan_barcode(
    input_data: BarcodeIn,
    user: user_dependency,
    db: db_dependency
):
    try:
        result = fetch_product_data(input_data.barcode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ API hatası: {str(e)}")

    if not result["found"]:
        raise HTTPException(status_code=404, detail="❌ Ürün bulunamadı")

    # DB’ye kaydet
    scan = ProductScan(
        barcode=result["barcode"],
        product_name=result["product_name"],
        gemini_report=str(result),  # Burada örnek olarak tüm veriyi saklıyoruz
        owner_id=user["id"]
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return {"scan_id": scan.id, "data": result}