from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite bağlantı URL'si
SQLALCHEMY_DATABASE_URL = "sqlite:///./greenlens.db"

# SQLite özel ayarı: aynı thread içinde çalışmayı zorunlu kılma
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Oturum (session) yöneticisi
SessionLocal = sessionmaker(
    autocommit=False,  # işlemleri otomatik commit etme
    autoflush=False,   # session.flush() otomatik çağrılmaz
    bind=engine        # bu session hangi engine'e bağlı
)

# SQLAlchemy Base sınıfı (model tanımları için)
Base = declarative_base()