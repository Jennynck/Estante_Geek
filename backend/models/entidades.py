from datetime import date, datetime
from sqlalchemy import (Boolean, Date, DateTime, Enum, 
                        ForeignKey, String, Text, UniqueConstraint, func,)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, FonteAPI, TipoObra

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_perfil: Mapped[str] = mapped_column(String(100))
    nome_usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    email_confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    foto: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(100))
    discord: Mapped[str | None] = mapped_column(String(100))
    x: Mapped[str | None] = mapped_column(String(100))
    perfil_publico: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    obras: Mapped[list["UsuarioObra"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    volumes: Mapped[list["UsuarioVolume"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

class Editora(Base):
    __tablename__ = "editoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True)

    obras: Mapped[list["Obra"]] = relationship(back_populates="editora")

class Genero(Base):
    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria: Mapped[str] = mapped_column(String(100), unique=True)

    # secondary recebe o NOME da tabela associativa que esta em associativas.py
    obras: Mapped[list["Obra"]] = relationship(
        secondary="obra_generos", back_populates="generos"
    )

class Obra(Base):
    __tablename__ = "obras"
    __table_args__ = (
        UniqueConstraint("fonte", "id_externo", name="uq_obras_fonte_id_externo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(250), index=True)
    sinopse: Mapped[str | None] = mapped_column(Text)
    capa_url: Mapped[str | None] = mapped_column(String(500))
    tipo_obra: Mapped[TipoObra] = mapped_column(Enum(TipoObra))
    total_volumes: Mapped[int | None]
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    editoras_id: Mapped[int | None] = mapped_column(ForeignKey("editoras.id"))

    fonte: Mapped[FonteAPI] = mapped_column(Enum(FonteAPI))
    id_externo: Mapped[str] = mapped_column(String(50))
    api_url: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    editora: Mapped["Editora | None"] = relationship(back_populates="obras")
    generos: Mapped[list["Genero"]] = relationship(
        secondary="obra_generos", back_populates="obras"
    )
    volumes: Mapped[list["Volume"]] = relationship(
        back_populates="obra", cascade="all, delete-orphan",
        order_by="Volume.numero_volume",
    )
    usuarios: Mapped[list["UsuarioObra"]] = relationship(
        back_populates="obra", cascade="all, delete-orphan"
    )

class Volume(Base):
    __tablename__ = "volumes"
    __table_args__ = (
        UniqueConstraint("obras_id", "numero_volume", name="uq_volumes_obra_numero"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    obras_id: Mapped[int] = mapped_column(ForeignKey("obras.id", ondelete="CASCADE"))
    numero_volume: Mapped[int]
    titulo_volume: Mapped[str | None] = mapped_column(String(250))
    sinopse: Mapped[str | None] = mapped_column(Text)
    capa_url: Mapped[str | None] = mapped_column(String(500))
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    id_externo: Mapped[str | None] = mapped_column(String(50))

    obra: Mapped["Obra"] = relationship(back_populates="volumes")
    usuarios: Mapped[list["UsuarioVolume"]] = relationship(
        back_populates="volume", cascade="all, delete-orphan"
    )

class Termo(Base):
    """Termos inadequados, usados para filtrar resenhas (moderação)."""
    __tablename__ = "termos"

    id: Mapped[int] = mapped_column(primary_key=True)
    termo_inadequado: Mapped[str] = mapped_column(String(100), unique=True)