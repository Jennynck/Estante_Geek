from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from models.base import StatusLeitura
from schemas.obra import ObraCatalogo

class UsuarioObraCreate(BaseModel):
    obras_id: int

# Alterar o status da obra
class UsuarioObraUpdate(BaseModel):
    status: StatusLeitura

class UsuarioObraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obra: ObraCatalogo
    status: StatusLeitura
    nota: int | None = None
    resenha: str | None = None
    data_publicacao: datetime
    volumes_lidos: int = 0   # volumes com status Lido
    progresso: float = 0.0   # volumes_lidos / total_volumes * 100

# Registrar ou editar a resenha (uma por obra)
class ResenhaCreate(BaseModel):
    nota: int = Field(ge=1, le=10)
    resenha: str | None = Field(default=None, max_length=500)

class AutorResenha(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome_perfil: str

class ResenhaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario: AutorResenha
    nota: int | None = None
    resenha: str | None = None
    data_publicacao: datetime

# Resenhas da obra com a média das notas
class ResenhasObra(BaseModel):
    media_notas: float | None = None
    total_avaliacoes: int
    resenhas: list[ResenhaResponse] = []
