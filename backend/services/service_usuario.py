import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Usuario
from schemas.usuario import UsuarioCreate, UsuarioLogin

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não está configurada no .env")


def gerarHash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode()[:72], bcrypt.gensalt()).decode()

def senhaConfere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode()[:72], senha_hash.encode())

class UsuarioService:
    # A senha é guardada criptografada (RNF01). E-mail e nome de perfil não podem se repetir
    # A confirmação do cadastro por e-mail (RN01) ainda não está implementada
    @staticmethod
    def cadastrar(db: Session, dados: UsuarioCreate) -> Usuario:
        email = dados.email.lower()
        if db.scalar(select(Usuario.id).where(Usuario.email == email)):
            raise HTTPException(409, "Este e-mail já está cadastrado")
        if db.scalar(select(Usuario.id).where(Usuario.nome_perfil == dados.nome_perfil)):
            raise HTTPException(409, "Este nome de perfil já está em uso")

        usuario = Usuario(**dados.model_dump(exclude={"email", "senha"}),
                          email=email, senha=gerarHash(dados.senha))
        db.add(usuario)
        db.commit()
        return usuario

    # O logout é feito pelo frontend, descartando o token
    @staticmethod
    def login(db: Session, dados: UsuarioLogin) -> dict:
        usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email.lower()))
        if not usuario or not senhaConfere(dados.senha, usuario.senha):
            raise HTTPException(401, "E-mail ou senha incorretos")

        expira = datetime.now(timezone.utc) + timedelta(hours=24)
        token = jwt.encode({"sub": str(usuario.id), "exp": expira}, SECRET_KEY, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}

    # Só usuários cadastrados e autenticados acessam a estante (RN02)
    @staticmethod
    def buscarPorToken(db: Session, token: str) -> Usuario:
        try:
            dados = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError:
            dados = {}
        usuario = db.get(Usuario, int(dados.get("sub", 0)))
        if not usuario:
            raise HTTPException(401, "Não autenticado", headers={"WWW-Authenticate": "Bearer"})
        return usuario
