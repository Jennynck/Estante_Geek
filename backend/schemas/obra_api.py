from datetime import datetime
from pydantic import BaseModel
from models.base import TipoObra

# Formato comum das obras vindas do Tenrai e do Comic Vine
class ObraAPI(BaseModel):
    api_url: str
    titulo: str
    sinopse: str | None = None
    capa_url: str | None = None
    tipo_obra: TipoObra
    total_volumes: int | None = None
    editora: str | None = None
    generos: list[str] = []
    data_publicacao: datetime | None = None
