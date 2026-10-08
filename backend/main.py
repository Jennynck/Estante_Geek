from fastapi import FastAPI
from database import engine
from models import Base

# Cria as tabelas no banco caso não existam
Base.metadata.create_all(bind=engine)
app = FastAPI()