from datetime import date
from pydantic import BaseModel, ConfigDict
# os dados vem das APIs e o usuário só consulta
class VolumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obras_id: int
    numero_volume: int
    titulo_volume: str | None = None
    sinopse: str | None = None
    capa_url: str | None = None
    data_publicacao: date | None = None