from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
# Lê a URL do banco que está no .env 
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
# Abre uma sessão para cada requisição e fecha no final
# Os endpoints recebem ela com Depends (get_db)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()