from pydantic import BaseModel, ConfigDict
from models.base import StatusLeitura
from schemas.volume import VolumeResponse

class UsuarioVolumeUpdate(BaseModel):
    possui_volume: bool | None = None
    status_leitura: StatusLeitura | None = None

class UsuarioVolumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume: VolumeResponse
    possui_volume: bool
    status_leitura: StatusLeitura

class ChecklistObra(BaseModel):
    obras_id: int
    total_volumes: int
    possuidos: int       # volumes marcados como possuídos
    faltantes: int       # total_volumes
    lidos: int           # volumes com status LIdo
    progresso: float     # lidos/total_volumes * 100 
    volumes: list[UsuarioVolumeResponse] = []

