import enum
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Classe base de todos os models do banco"""
    pass

class TipoObra(str, enum.Enum):
    HQ = "HQ"
    MANGA = "Manga"

class FonteAPI(str, enum.Enum):
    JIKAN = "jikan"
    COMICVINE = "comicvine"

class StatusLeitura(str, enum.Enum):
    QUERO_LER = "Quero ler"
    LENDO = "Lendo"
    LIDO = "Lido"
    PAUSADO = "Pausado"