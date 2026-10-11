from pydantic import BaseModel, ConfigDict
from models.base import StatusLeitura
from schemas.obra import ObraCatalogo
from schemas.volume import VolumeResponse

class UsuarioVolumeUpdate(BaseModel):
    possui_volume: bool | None = None
    status_leitura: StatusLeitura | None = None

class UsuarioVolumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    volume: VolumeResponse
    possui_volume: bool
    status_leitura: StatusLeitura

# Checklist e progresso da obra
class ChecklistObra(BaseModel):
    obra: ObraCatalogo
    status: StatusLeitura   # status da obra na estante
    total_volumes: int
    possuidos: int       # volumes marcados como possuídos
    faltantes: int       # total_volumes - possuidos
    lidos: int           # volumes com status Lido
    progresso: float     # lidos / total_volumes * 100
    volumes: list[UsuarioVolumeResponse] = []
