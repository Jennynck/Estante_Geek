from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from models.base import StatusLeitura
from schemas.obra import ObraResponse

class UsuarioObraUpdate(BaseModel):
    obras_id: int

class UsuarioObraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obra: ObraResponse
    status: StatusLeitura | None = None
    nota: int | None = None
    resenha: str | None = None
    adicionada_em: datetime

# Registrar nota e resenha
class ResenhaCreate(BaseModel):
    nota: int = Field(ge=1, le=10)
    resenha: str | None = Field(default=None, max_length=500)

# Alterar senha existente
class ResenhaUpdate(BaseModel):
    nota: int | None = Field(default=None, ge=1, le=10)
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
    data_resenha: datetime | None = None

class ResenhasObra(BaseModel):
    media_notas: float | None = None
    total_avaliacoes: int
    resenhas: list[ResenhaResponse] = []