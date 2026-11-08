from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from models import Obra, Usuario, UsuarioObra
from schemas.obra import ObraCatalogo
from services.service_catalogo import CatalogoService

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