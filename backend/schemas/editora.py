from pydantic import BaseModel, ConfigDict

# Lista usada no filtro do catálogo
class EditoraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
