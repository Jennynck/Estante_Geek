import re
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, contains_eager, joinedload
from models import Obra, Termo, UsuarioObra, UsuarioVolume, Volume
from models.base import StatusLeitura
from schemas.usuario_obra import ResenhaCreate, UsuarioObraResponse
from schemas.usuario_volume import ChecklistObra, UsuarioVolumeResponse
from services.service_catalogo import CatalogoService

# Mudanças de status permitidas em cada volume
TRANSICOES = {
    StatusLeitura.QUERO_LER: {StatusLeitura.LENDO},
    StatusLeitura.LENDO: {StatusLeitura.LIDO, StatusLeitura.PAUSADO},
    StatusLeitura.PAUSADO: {StatusLeitura.LENDO, StatusLeitura.LIDO},
    StatusLeitura.LIDO: {StatusLeitura.LENDO}   # releitura
}

# Progresso = volumes lidos / total de volumes
def calcularProgresso(lidos: int, total: int) -> float:
    return round(lidos / total * 100, 1) if total else 0.0

class EstanteService:
    # Estante do usuário com o progresso de leitura de cada obra
    @staticmethod
    def listar(db: Session, usuario_id: int, obras_id: int | None = None) -> list[UsuarioObraResponse]:
        consulta = (select(UsuarioObra).where(UsuarioObra.usuarios_id == usuario_id)
                    .options(joinedload(UsuarioObra.obra).joinedload(Obra.editora),
                             joinedload(UsuarioObra.obra).selectinload(Obra.generos))
                    .order_by(UsuarioObra.id.desc()))
        if obras_id:
            consulta = consulta.where(UsuarioObra.obras_id == obras_id)
        registros = list(db.scalars(consulta))

        catalogo = {c.id: c for c in CatalogoService.montar(db, [r.obra for r in registros])}
        lidos = dict(db.execute(
            select(Volume.obras_id, func.count())
            .join(UsuarioVolume, UsuarioVolume.volumes_id == Volume.id)
            .where(UsuarioVolume.usuarios_id == usuario_id,
                   UsuarioVolume.status_leitura == StatusLeitura.LIDO)
            .group_by(Volume.obras_id)).all())

        itens = []
        for r in registros:
            obra = catalogo[r.obras_id]
            obra.na_estante = True
            volumes_lidos = lidos.get(r.obras_id, 0)
            itens.append(UsuarioObraResponse(
                id=r.id, obra=obra, status=r.status, nota=r.nota, resenha=r.resenha,
                data_publicacao=r.data_publicacao, volumes_lidos=volumes_lidos,
                progresso=calcularProgresso(volumes_lidos, obra.total_volumes)))
        return itens

    # A mesma obra não pode entrar duas vezes na estante (RN10)
    # Cria também uma linha de checklist para cada volume da obra
    @staticmethod
    def adicionar(db: Session, usuario_id: int, obras_id: int) -> UsuarioObraResponse:
        if not db.get(Obra, obras_id):
            raise HTTPException(404, "Obra não encontrada")
        if db.scalar(select(UsuarioObra.id).where(
                UsuarioObra.usuarios_id == usuario_id, UsuarioObra.obras_id == obras_id)):
            raise HTTPException(409, "Esta obra já está na sua estante")

        db.add(UsuarioObra(usuarios_id=usuario_id, obras_id=obras_id))
        for volumes_id in db.scalars(select(Volume.id).where(Volume.obras_id == obras_id)):
            db.add(UsuarioVolume(usuarios_id=usuario_id, volumes_id=volumes_id))
        db.commit()
        return EstanteService.listar(db, usuario_id, obras_id)[0]

    # Cada obra tem um único status por usuário, o novo substitui o anterior (RN14)
    @staticmethod
    def atualizarStatus(db: Session, usuario_id: int, obras_id: int, status: StatusLeitura) -> UsuarioObraResponse:
        EstanteService._buscarRegistro(db, usuario_id, obras_id).status = status
        db.commit()
        return EstanteService.listar(db, usuario_id, obras_id)[0]

    # Remove a obra da estante junto com o checklist dela (RF04)
    @staticmethod
    def remover(db: Session, usuario_id: int, obras_id: int) -> None:
        registro = EstanteService._buscarRegistro(db, usuario_id, obras_id)
        volumes = select(Volume.id).where(Volume.obras_id == obras_id)
        db.execute(delete(UsuarioVolume).where(
            UsuarioVolume.usuarios_id == usuario_id, UsuarioVolume.volumes_id.in_(volumes)))
        db.delete(registro)
        db.commit()

    # Checklist: considera possuídos só os volumes marcados e faltantes os demais (RF06 e RN08)
    @staticmethod
    def checklist(db: Session, usuario_id: int, obras_id: int) -> ChecklistObra:
        registro = EstanteService._buscarRegistro(db, usuario_id, obras_id)
        linhas = list(db.scalars(
            select(UsuarioVolume).join(UsuarioVolume.volume)
            .options(contains_eager(UsuarioVolume.volume))
            .where(UsuarioVolume.usuarios_id == usuario_id, Volume.obras_id == obras_id)
            .order_by(Volume.numero_volume)))

        total = len(linhas)
        possuidos = sum(1 for l in linhas if l.possui_volume)
        lidos = sum(1 for l in linhas if l.status_leitura == StatusLeitura.LIDO)
        obra = CatalogoService.montar(db, [registro.obra])[0]
        obra.na_estante = True
        return ChecklistObra(
            obra=obra, status=registro.status, total_volumes=total, possuidos=possuidos,
            faltantes=total - possuidos, lidos=lidos, progresso=calcularProgresso(lidos, total),
            volumes=[UsuarioVolumeResponse.model_validate(l) for l in linhas])

    # Marcar ou desmarcar o volume atualiza o checklist (RN11). O status segue as transições de RN07
    @staticmethod
    def atualizarVolume(db: Session, usuario_id: int, obras_id: int, volumes_id: int,
                         possui_volume: bool | None, status_leitura: StatusLeitura | None) -> UsuarioVolume:
        EstanteService._buscarRegistro(db, usuario_id, obras_id)
        linha = db.scalar(
            select(UsuarioVolume).join(UsuarioVolume.volume)
            .where(UsuarioVolume.usuarios_id == usuario_id, UsuarioVolume.volumes_id == volumes_id,
                   Volume.obras_id == obras_id))
        if not linha:
            raise HTTPException(404, "Volume não encontrado nesta obra")

        if status_leitura and status_leitura != linha.status_leitura:
            if status_leitura not in TRANSICOES[linha.status_leitura]:
                raise HTTPException(400, f"Não é possível mudar o volume de "
                                         f"'{linha.status_leitura.value}' para '{status_leitura.value}'")
            linha.status_leitura = status_leitura
        if possui_volume is not None:
            linha.possui_volume = possui_volume
        db.commit()
        return linha

    # Uma resenha por obra: enviar de novo atualiza a existente (RN13)
    # Textos com termos da lista de palavras inadequadas são bloqueados (RN09)
    @staticmethod
    def salvarResenha(db: Session, usuario_id: int, obras_id: int, dados: ResenhaCreate) -> UsuarioObra:
        registro = EstanteService._buscarRegistro(db, usuario_id, obras_id)
        if dados.resenha and EstanteService._temTermoInadequado(db, dados.resenha):
            raise HTTPException(400, "A resenha contém termos inadequados")

        registro.nota = dados.nota
        registro.resenha = dados.resenha or None
        registro.data_publicacao = datetime.now()   # data em que a resenha foi publicada
        db.commit()
        return registro

    @staticmethod
    def _buscarRegistro(db: Session, usuario_id: int, obras_id: int) -> UsuarioObra:
        registro = db.scalar(select(UsuarioObra).where(
            UsuarioObra.usuarios_id == usuario_id, UsuarioObra.obras_id == obras_id))
        if not registro:
            raise HTTPException(404, "Esta obra não está na estante")
        return registro

    # Compara palavra inteira, ignorando maiúsculas e minúsculas
    @staticmethod
    def _temTermoInadequado(db: Session, texto: str) -> bool:
        return any(re.search(rf"\b{re.escape(termo)}\b", texto, re.IGNORECASE)
                   for termo in db.scalars(select(Termo.termos_inadequados)))
