from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base     # → SQLAlchemy engine+Base, ayrı dosya

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(50), unique=True, index=True, nullable=False)
    email      = Column(String(100), unique=True, index=True, nullable=False)
    password   = Column(String,  nullable=False)
    is_active  = Column(Boolean, default=True)
    role       = Column(String(20), default="user")
    # ilişkiler
    scans      = relationship("ProductScan", back_populates="owner")
    crises     = relationship("CrisisSim",   back_populates="owner")

class ProductScan(Base):
    __tablename__ = "product_scans"
    id            = Column(Integer, primary_key=True, index=True)
    barcode       = Column(String,  nullable=True)      # barkod yoksa NULL
    product_name  = Column(String,  nullable=True)
    gemini_report = Column(JSON)       # PFAS / palm / CO2 özetinin tamamı
    owner_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    owner         = relationship("User", back_populates="scans")

class CrisisSim(Base):
    __tablename__ = "crisis_sims"
    id         = Column(Integer, primary_key=True, index=True)
    crisis     = Column(String, nullable=False)      # “su krizi”, “plastik”
    scenarios  = Column(JSON)   # {2030:{txt,img}, 2050:{}, 2100:{}}
    owner_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner      = relationship("User", back_populates="crises")