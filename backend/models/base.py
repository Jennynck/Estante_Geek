import enum
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Classe base de todos os models do banco"""
    pass

class TipoObra(str, enum.Enum):
    HQ = "HQ"
    MANGA = "Manga"

class StatusLeitura(str, enum.Enum):
    QUERO_LER = "Quero Ler"
    LENDO = "Lendo"
    LIDO = "Lido"
    PAUSADO = "Pausado"

# Faz o banco salvar o texto do status "Quero Ler"
def valores_enum(classe_enum):
    return [item.value for item in classe_enum]
