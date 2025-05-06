import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User


SECRET_KEY  = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM   = os.getenv("ALGORITHM",  "HS256")
TOKEN_EX_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserIn(BaseModel):
    username: str = Field(..., min_length=3)
    email:    str = Field(..., min_length=5, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)

class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"


def _create_access_token(data: dict, minutes: int | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or TOKEN_EX_MIN
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def _authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user and pwd_ctx.verify(password, user.password):
        return user
    return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int | None = payload.get("id")
        if user_id is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise cred_exc
    return user


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_in: UserIn, db: Session = Depends(get_db)):
    if db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first():
        raise HTTPException(400, "Username or email already registered")
    user = User(
        username=user_in.username,
        email=user_in.email,
        password=pwd_ctx.hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", "user_id": user.id}

@router.post("/token", response_model=TokenOut)
def login_for_access_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session = Depends(get_db)
):
    user = _authenticate(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = _create_access_token({"sub": user.username, "id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenOut)
def login_json(user_in: UserIn, db: Session = Depends(get_db)):
    user = _authenticate(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = _create_access_token({"sub": user.username, "id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id":       current_user.id,
        "username": current_user.username,
        "email":    current_user.email,
    }