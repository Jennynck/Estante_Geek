from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload, defer
from models import Termo, UsuarioObra
from schemas.termo import TermoCreate
from models.entidades import Usuario
from schemas.admin import UsuarioAdmin

class AdminService:
    # Só o administrador gerencia a lista de palavras inadequadas (RN17)
    @staticmethod
    def listarTermos(db: Session) -> list[Termo]:
        return list(db.scalars(select(Termo).order_by(Termo.termos_inadequados)))

    # O filtro das resenhas ignora maiúsculas, então o termo é salvo em minúsculas
    # e a repetição é checada sem diferenciar maiúsculas de minúsculas
    @staticmethod
    def adicionarTermo(db: Session, dados: TermoCreate) -> Termo:
        texto = dados.termos_inadequados.strip().lower()
        if len(texto) < 2:
            raise HTTPException(422, "O termo deve ter pelo menos 2 caracteres")
        if any(t.lower() == texto for t in db.scalars(select(Termo.termos_inadequados))):
            raise HTTPException(409, "Este termo já está na lista")
        if not any(c.isalpha() for c in texto):
            raise HTTPException(422, "O termo deve conter pelo menos uma letra")

        termo = Termo(termos_inadequados=texto)
        db.add(termo)
        db.commit()
        return termo

    @staticmethod
    def removerTermo(db: Session, termos_id: int) -> None:
        termo = db.get(Termo, termos_id)
        if not termo:
            raise HTTPException(404, "Termo não encontrado")
        db.delete(termo)
        db.commit()

    # Resenhas de todos os usuários para moderação (RN16). Só entram registros com nota
    @staticmethod
    def listarResenhas(db: Session, busca: str | None = None, obras_id: int | None = None,
                       usuarios_id: int | None = None, pagina: int = 1, limite: int = 20) -> list[UsuarioObra]:
        pagina, limite = max(pagina, 1), min(max(limite, 1), 50)
        consulta = (select(UsuarioObra)
                    .options(joinedload(UsuarioObra.usuario), joinedload(UsuarioObra.obra))
                    .where(UsuarioObra.nota.is_not(None))
                    .order_by(UsuarioObra.data_publicacao.desc(), UsuarioObra.id.desc()))
        if busca and busca.strip():
            consulta = consulta.where(UsuarioObra.resenha.ilike(f"%{busca.strip()[:100]}%"))
        if obras_id:
            consulta = consulta.where(UsuarioObra.obras_id == obras_id)
        if usuarios_id:
            consulta = consulta.where(UsuarioObra.usuarios_id == usuarios_id)
        return list(db.scalars(consulta.offset((pagina - 1) * limite).limit(limite)))

    # Bloquear não apaga: a resenha fica guardada e escondida, e pode ser liberada de novo (RN16)
    @staticmethod
    def bloquearResenha(db: Session, usuarios_obras_id: int, bloqueada: bool) -> UsuarioObra:
        registro = db.scalar(select(UsuarioObra)
                             .options(joinedload(UsuarioObra.usuario), joinedload(UsuarioObra.obra))
                             .where(UsuarioObra.id == usuarios_obras_id))
        if not registro or registro.nota is None:
            raise HTTPException(404, "Resenha não encontrada")
        registro.resenha_bloqueada = bloqueada
        db.commit()
        return registro

    # Lista os usuários para o administrador, com busca por nome de perfil ou e-mail (RF14)
    @staticmethod
    def listarUsuarios(db: Session, busca: str | None = None,
                       pagina: int = 1, limite: int = 20) -> list[Usuario]:
        pagina, limite = max(pagina, 1), min(max(limite, 1), 50)
        consulta = select(Usuario).options(defer(Usuario.foto)).order_by(Usuario.id)  # não carrega a foto
        if busca and busca.strip():
            termo = f"%{busca.strip()[:100]}%"
            consulta = consulta.where(or_(Usuario.nome_perfil.ilike(termo),
                                          Usuario.email.ilike(termo)))
        return list(db.scalars(consulta.offset((pagina - 1) * limite).limit(limite)))
    