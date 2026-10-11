from pydantic import BaseModel, ConfigDict

# Lista usada no filtro do catálogo
class GeneroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria: str
