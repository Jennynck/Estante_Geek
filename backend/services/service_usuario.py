import logging
import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Usuario
from schemas.usuario import UsuarioCreate, UsuarioLogin, UsuarioUpdate
from services.service_email import EmailError, EmailService

log = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não está configurada no .env")
FRONTEND_URL = (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")

def gerarHash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode()[:72], bcrypt.gensalt()).decode()

def senhaConfere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode()[:72], senha_hash.encode())

class UsuarioService:
    # A senha é guardada criptografada (RNF01). E-mail e nome de perfil não podem se repetir
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

    # Só usuários cadastrados e autenticados acessam a estante
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

    @staticmethod
    def enviarConfirmacao(usuario_id: int, email: str, nome: str) -> None:
        expira = datetime.now(timezone.utc) + timedelta(hours=24)
        token = jwt.encode({"sub": str(usuario_id), "tipo": "confirmar_email",
                            "email": email, "exp": expira}, SECRET_KEY, algorithm="HS256")
        link = f"{FRONTEND_URL}/confirmar-email?token={token}"
        texto = (f"Olá, {nome}!\n\nConfirme seu e-mail para ativar sua conta na Estante Geek:\n"
                 f"{link}\n\nO link vale por 24 horas. Se não foi você, ignore esta mensagem.")
        html = (f"<p>Olá, <b>{nome}</b>!</p>"
                f"<p>Confirme seu e-mail para ativar sua conta na Estante Geek:</p>"
                f'<p><a href="{link}">Confirmar meu e-mail</a></p>'
                f"<p>O link vale por 24 horas. Se não foi você, ignore esta mensagem.</p>")
        try:
            EmailService.enviar(email, "Confirme seu e-mail - Estante Geek", texto, html)
        except EmailError as erro:
            log.error("Não foi possível enviar a confirmação para %s: %s", email, erro)

    # Valida o link recebido por e-mail e marca o e-mail como confirmado (RN01)
    @staticmethod
    def confirmarEmail(db: Session, token: str) -> None:
        try:
            dados = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(400, "Este link expirou. Solicite um novo link de confirmação.")
        except jwt.PyJWTError:
            raise HTTPException(400, "Link de confirmação inválido.")
        if dados.get("tipo") != "confirmar_email":
            raise HTTPException(400, "Link de confirmação inválido.")

        usuario = db.get(Usuario, int(dados.get("sub", 0)))
        if not usuario or usuario.email != dados.get("email"):
            raise HTTPException(400, "Link de confirmação inválido.")
        if not usuario.email_confirmado:
            usuario.email_confirmado = True
            db.commit()

    # Devolve o usuário só se existir e ainda não estiver confirmado
    @staticmethod
    def pendenteDeConfirmacao(db: Session, email: str) -> Usuario | None:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email.lower()))
        return usuario if usuario and not usuario.email_confirmado else None

# A conta só pode entrar depois de confirmar o e-mail
    @staticmethod
    def login(db: Session, dados: UsuarioLogin) -> dict:
        usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email.lower()))
        if not usuario or not senhaConfere(dados.senha, usuario.senha):
            raise HTTPException(401, "E-mail ou senha incorretos")
        if not usuario.email_confirmado:
            raise HTTPException(403, "Confirme seu e-mail antes de entrar. Verifique sua caixa de entrada.")

        expira = datetime.now(timezone.utc) + timedelta(hours=24)
        token = jwt.encode({"sub": str(usuario.id), "tipo": "acesso", "exp": expira},
                           SECRET_KEY, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}

# Edição do perfil: só altera o que o usuário enviou (RF11/RN06)
# Um contato enviado vazio ou null é removido (o schema converte "" em None)
    @staticmethod
    def atualizarPerfil(db: Session, usuario: Usuario, dados: UsuarioUpdate) -> Usuario:
        campos = dados.model_dump(exclude_unset=True)   # ignora o que não foi enviado

        # Estes campos podem ser alterados, mas nunca apagados
        for obrigatorio in ("nome_perfil", "nome_usuario", "perfil_publico"):
            if obrigatorio in campos:
                valor = campos[obrigatorio]
                if isinstance(valor, str):
                    valor = campos[obrigatorio] = valor.strip()
                if valor is None or valor == "":
                    raise HTTPException(422, f"O campo {obrigatorio} não pode ficar vazio")

        novo_perfil = campos.get("nome_perfil")
        if novo_perfil and novo_perfil != usuario.nome_perfil:
            if db.scalar(select(Usuario.id).where(
                    Usuario.nome_perfil == novo_perfil, Usuario.id != usuario.id)):
                raise HTTPException(409, "Este nome de perfil já está em uso")

        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        db.commit()
        db.refresh(usuario)
        return usuario

# Exclui a conta e em cascata a estante, o checklist e as resenhas (RF17)
    @staticmethod
    def excluirConta(db: Session, usuario: Usuario, senha: str) -> None:
        if usuario.is_admin:
            raise HTTPException(403, "O administrador não pode excluir a própria conta")
        if not senhaConfere(senha, usuario.senha):
            raise HTTPException(403, "Senha incorreta")
        db.delete(usuario)
        db.commit()