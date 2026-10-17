from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from models import Editora, Genero, Obra, UsuarioObra, Volume
from models.base import TipoObra
from schemas.obra import ObraCatalogo, ObraDetalhe
from schemas.obra_api import ObraAPI
from schemas.usuario_obra import ResenhaResponse, ResenhasObra
from schemas.volume import VolumeResponse
from services.service_comic_vine import ComicVineError, ComicVineService
from services.service_tenrai import TenraiError, TenraiService

class CatalogoService:
    # Catálogo com busca por nome e filtros de tipo e editora (RF03)
    @staticmethod
    def listar(db: Session, busca: str | None = None, tipo: TipoObra | None = None,
               editora: str | None = None, pagina: int = 1, limite: int = 20) -> list[ObraCatalogo]:
        busca = busca.strip()[:100] if busca else None
        pagina, limite = max(pagina, 1), min(max(limite, 1), 25)
        try:
            obras = CatalogoService.buscar(db, busca, tipo, editora, pagina, limite)
        except (TenraiError, ComicVineError) as erro:
            raise HTTPException(502, str(erro))
        return CatalogoService.montar(db, obras)

    # Detalhes da obra com os volumes (RF05)
    @staticmethod
    def detalhar(db: Session, obras_id: int) -> ObraDetalhe:
        obra = db.get(Obra, obras_id)
        if not obra:
            raise HTTPException(404, "Obra não encontrada")
        catalogo = CatalogoService.montar(db, [obra])[0]
        return ObraDetalhe(**catalogo.model_dump(),
                           volumes=[VolumeResponse.model_validate(v) for v in obra.volumes])

    # Resenhas da obra com a média das notas (RF09 e RN19)
    @staticmethod
    def resenhas(db: Session, obras_id: int) -> ResenhasObra:
        if not db.get(Obra, obras_id):
            raise HTTPException(404, "Obra não encontrada")
        registros = db.scalars(
            select(UsuarioObra).options(joinedload(UsuarioObra.usuario))
            .where(UsuarioObra.obras_id == obras_id, UsuarioObra.nota.is_not(None))
            .order_by(UsuarioObra.data_publicacao.desc())).all()
        media = round(sum(r.nota for r in registros) / len(registros), 1) if registros else None
        return ResenhasObra(media_notas=media, total_avaliacoes=len(registros),
                            resenhas=[ResenhaResponse.model_validate(r) for r in registros])

    # Só consulta as APIs quando o banco não tem nada para a busca (RNF08)
    @staticmethod
    def buscar(db: Session, busca: str | None, tipo: TipoObra | None, editora: str | None,
               pagina: int, limite: int) -> list[Obra]:
        obras = CatalogoService._buscarNoBanco(db, busca, tipo, editora, pagina, limite)
        if busca and not obras:
            CatalogoService._importar(db, busca, tipo, pagina, limite)
            obras = CatalogoService._buscarNoBanco(db, busca, tipo, editora, pagina, limite)
        return obras

    @staticmethod
    def _buscarNoBanco(db: Session, busca, tipo, editora, pagina, limite) -> list[Obra]:
        consulta = (select(Obra).options(joinedload(Obra.editora), selectinload(Obra.generos))
                    .order_by(Obra.titulo))
        if busca:
            consulta = consulta.where(Obra.titulo.ilike(f"%{busca}%"))
        if tipo:
            consulta = consulta.where(Obra.tipo_obra == tipo)
        if editora:
            consulta = consulta.where(Obra.editora.has(Editora.nome.ilike(f"%{editora}%")))
        return list(db.scalars(consulta.offset((pagina - 1) * limite).limit(limite)))

    # Mangás vêm do Tenrai (RNF05) e HQs do Comic Vine (RNF06). Se uma API falhar, o erro sobe para listar
    @staticmethod
    def _importar(db: Session, busca: str, tipo: TipoObra | None, pagina: int, limite: int) -> None:
        if tipo in (None, TipoObra.MANGA):
            for obra_api in TenraiService.buscarMangas(busca, pagina, limite):
                CatalogoService.salvar(db, obra_api)
            db.commit()
        if tipo in (None, TipoObra.HQ):
            for obra_api in ComicVineService.buscarHqs(busca, pagina, limite):
                CatalogoService.salvar(db, obra_api)
            db.commit()

    # Guarda a obra no banco (RNF07). Obras já salvas (mesma api_url) são reaproveitadas
    @staticmethod
    def salvar(db: Session, obra_api: ObraAPI) -> Obra:
        obra = db.scalar(select(Obra).where(Obra.api_url == obra_api.api_url))
        if obra:
            return obra

        editora = None
        if obra_api.editora:
            editora = (db.scalar(select(Editora).where(Editora.nome == obra_api.editora))
                       or Editora(nome=obra_api.editora))

        generos = [db.scalar(select(Genero).where(Genero.categoria == nome)) or Genero(categoria=nome)
                   for nome in set(obra_api.generos)]

        obra = Obra(
            titulo=obra_api.titulo, sinopse=obra_api.sinopse, capa_url=obra_api.capa_url,
            tipo_obra=obra_api.tipo_obra, api_url=obra_api.api_url,
            editora=editora, generos=generos,
            # As APIs só informam quantos volumes existem, então eles são numerados de 1 até o total
            volumes=[Volume(numero_volume=n, titulo_volume=f"Volume {n}", capa_url=obra_api.capa_url)
                     for n in range(1, (obra_api.total_volumes or 0) + 1)],
        )
        if obra_api.data_publicacao:
            obra.data_publicacao = obra_api.data_publicacao
        db.add(obra)
        db.flush()   # grava já a editora e os gêneros novos para a próxima obra reaproveitá-los
        return obra

    # Converte as obras do banco para o formato devolvido pela API, com total de volumes e média das notas
    @staticmethod
    def montar(db: Session, obras: list[Obra]) -> list[ObraCatalogo]:
        ids = [o.id for o in obras]
        totais = dict(db.execute(
            select(Volume.obras_id, func.count()).where(Volume.obras_id.in_(ids))
            .group_by(Volume.obras_id)).all())
        medias = {linha[0]: (linha[1], linha[2]) for linha in db.execute(
            select(UsuarioObra.obras_id, func.avg(UsuarioObra.nota), func.count(UsuarioObra.nota))
            .where(UsuarioObra.obras_id.in_(ids), UsuarioObra.nota.is_not(None))
            .group_by(UsuarioObra.obras_id)).all()}

        catalogo = []
        for o in obras:
            media, avaliacoes = medias.get(o.id, (None, 0))
            catalogo.append(ObraCatalogo(
                id=o.id, titulo=o.titulo, sinopse=o.sinopse, capa_url=o.capa_url, tipo_obra=o.tipo_obra,
                total_volumes=totais.get(o.id, 0), data_publicacao=o.data_publicacao, api_url=o.api_url,
                editora=o.editora.nome if o.editora else None,
                generos=sorted(g.categoria for g in o.generos),
                media_notas=round(float(media), 1) if media is not None else None,
                total_avaliacoes=avaliacoes))
        return catalogo
