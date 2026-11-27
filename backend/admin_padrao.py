import os
from sqlalchemy import select
from database import SessionLocal
from models import Usuario
from services.service_usuario import gerarHash

# Cria o administrador padrão se o banco ainda não tiver nenhum
def criarAdminPadrao() -> None:
    email = os.getenv("ADMIN_EMAIL")
    senha = os.getenv("ADMIN_SENHA")
    nome_perfil = os.getenv("ADMIN_NOME_PERFIL")

    if not (email and senha and nome_perfil):
        print("Administrador padrão não criado: configure ADMIN_EMAIL, ADMIN_SENHA e ADMIN_NOME_PERFIL no .env")
        return

    db = SessionLocal()
    try:
        # se já existe algum administrador, não faz nada
        if db.scalar(select(Usuario.id).where(Usuario.is_admin.is_(True)).limit(1)):
            return

        # caso o e-mail ou o nome de perfil já estejam em uso
        em_uso = db.scalar(select(Usuario.id).where(
            (Usuario.email == email.lower()) | (Usuario.nome_perfil == nome_perfil)))
        if em_uso:
            print("E-mail ou nome de perfil já está em uso")
            return

        admin = Usuario(
            nome_perfil=nome_perfil,
            nome_usuario="Administrador",
            email=email.lower(),
            senha=gerarHash(senha),
            email_confirmado=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        print(f"Administrador padrão criado: {email}")
    finally:
        db.close()