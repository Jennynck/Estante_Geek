from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from models import Obra, Usuario, UsuarioObra
from schemas.obra import ObraCatalogo
from services.service_catalogo import CatalogoService
from schemas.usuario import LeitorAfinidade

class AfinidadeService:
    # Obras que estão na estante dos dois usuários (RN12)
    # Funciona mesmo com o perfil do outro privado: só mostra obras que o próprio usuário já tem
    @staticmethod
    def obrasEmComum(db: Session, logado_id: int, usuarios_id: int) -> list[ObraCatalogo]:
        if not db.get(Usuario, usuarios_id):
            raise HTTPException(404, "Usuário não encontrado")
        if usuarios_id == logado_id:
            raise HTTPException(400, "Escolha outro usuário para comparar as estantes")

        minhas = select(UsuarioObra.obras_id).where(UsuarioObra.usuarios_id == logado_id)
        obras = list(db.scalars(
            select(Obra).options(joinedload(Obra.editora), selectinload(Obra.generos))
            .join(UsuarioObra, UsuarioObra.obras_id == Obra.id)
            .where(UsuarioObra.usuarios_id == usuarios_id, Obra.id.in_(minhas))
            .order_by(Obra.titulo)))

        catalogo = CatalogoService.montar(db, obras)
        for obra in catalogo:
            obra.na_estante = True   # todas já estão na estante de quem consulta
        return catalogo

    # Leitores com obras em comum com o usuário logado, do mais ao menos parecido (RF10 e RN12)
    # Contatos externos só aparecem para perfis públicos (RN06)
    @staticmethod
    def leitores(db: Session, logado_id: int, pagina: int = 1, limite: int = 20) -> list[LeitorAfinidade]:
        pagina, limite = max(pagina, 1), min(max(limite, 1), 50)

        # Quem consulta precisa ter pelo menos uma obra na estante
        minhas = select(UsuarioObra.obras_id).where(UsuarioObra.usuarios_id == logado_id)
        if not db.scalar(minhas.limit(1)):
            raise HTTPException(400, "Adicione pelo menos uma obra à sua estante para descobrir leitores")

        # Seleciona só as colunas necessárias sem carregar a foto de cada usuário
        linhas = db.execute(
            select(Usuario.id, Usuario.nome_perfil, Usuario.perfil_publico,
                   Usuario.instagram, Usuario.discord, Usuario.x, Obra.titulo)
            .join(UsuarioObra, UsuarioObra.usuarios_id == Usuario.id)
            .join(Obra, Obra.id == UsuarioObra.obras_id)
            .where(Usuario.id != logado_id, UsuarioObra.obras_id.in_(minhas))
            .order_by(Obra.titulo)).all()

        leitores: dict[int, LeitorAfinidade] = {}
        for usuario_id, nome_perfil, publico, instagram, discord, x, titulo in linhas:
            leitor = leitores.get(usuario_id)
            if not leitor:
                leitor = leitores[usuario_id] = LeitorAfinidade(
                    id=usuario_id, nome_perfil=nome_perfil, perfil_publico=publico,
                    instagram=instagram if publico else None,
                    discord=discord if publico else None,
                    x=x if publico else None,
                    total_em_comum=0, obras_em_comum=[])
            leitor.obras_em_comum.append(titulo)
            leitor.total_em_comum += 1

        ordenados = sorted(leitores.values(), key=lambda l: (-l.total_em_comum, l.nome_perfil.lower()))
        inicio = (pagina - 1) * limite
        return ordenados[inicio:inicio + limite]