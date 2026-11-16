from datetime import date
from pydantic import BaseModel, ConfigDict
from models.base import TipoObra
from schemas.usuario_obra import AutorResenha

class ObraResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    tipo_obra: TipoObra

# Resenha vista pelo administrador, com a obra e o autor
class ResenhaModeracao(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int   # id do registro em usuarios_obras
    usuario: AutorResenha
    obra: ObraResumo
    nota: int | None = None
    resenha: str | None = None
    resenha_bloqueada: bool = False
    data_publicacao: date

class ResenhaBloqueio(BaseModel):
    bloqueada: bool