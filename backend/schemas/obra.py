from datetime import datetime
from pydantic import BaseModel, ConfigDict
from models.base import StatusLeitura, TipoObra
from schemas.volume import VolumeResponse

class ObraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    sinopse: str | None = None
    capa_url: str | None = None
    tipo_obra: TipoObra
    total_volumes: int
    data_publicacao: datetime
    api_url: str

# Obra no catálogo e na estante
class ObraCatalogo(ObraResponse):
    editora: str | None = None
    generos: list[str] = []
    media_notas: float | None = None
    total_avaliacoes: int = 0
    na_estante: bool = False   # se a obra já está na estante de quem consulta

# Tela de detalhes da obra
class ObraDetalhe(ObraCatalogo):
    status: StatusLeitura | None = None
    volumes: list[VolumeResponse] = []