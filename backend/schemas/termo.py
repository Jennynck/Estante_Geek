from pydantic import BaseModel, ConfigDict, Field

# Lista de palavras inadequadas, gerenciada pelo administrador
class TermoCreate(BaseModel):
    termos_inadequados: str = Field(min_length=2, max_length=100)

class TermoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    termos_inadequados: str
