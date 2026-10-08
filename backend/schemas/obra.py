from datetime import date
from pydantic import BaseModel, ConfigDict
from models.base import TipoObra
from schemas.volume import VolumeResponse
# Obra no catálogo e na estante
class ObraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    sinopse: str | None = None
    capa_url: str | None = None
    tipo_obra: TipoObra
    total_volumes: int | None = None
    data_publicacao: date | None = None
    api_url: str | None = None
# Tela de detalhes da obra
class ObraDetalhe(ObraResponse):
    volumes: list[VolumeResponse] = []