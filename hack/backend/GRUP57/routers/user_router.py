# routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Kullanıcı adı zaten kayıtlı")

    password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Kayıt başarılı", "user_id": db_user.id}
