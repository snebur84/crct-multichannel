import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Dica: adicione um fallback caso a env não esteja carregada
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://crctx_user:crctx_pass@pbx-db:5432/crctx_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()