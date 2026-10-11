from datetime import datetime
from sqlalchemy import (Boolean, DateTime, Enum, ForeignKey, LargeBinary,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TipoObra

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_perfil: Mapped[str] = mapped_column(String(50), unique=True)
    nome_usuario: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    senha: Mapped[str] = mapped_column(String(250))
    email_confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    foto: Mapped[bytes | None] = mapped_column(LargeBinary)
    instagram: Mapped[str | None] = mapped_column(String(50))
    discord: Mapped[str | None] = mapped_column(String(50))
    x: Mapped[str | None] = mapped_column(String(50))
    perfil_publico: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    obras: Mapped[list["UsuarioObra"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    volumes: Mapped[list["UsuarioVolume"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

class Editora(Base):
    __tablename__ = "editoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)

    obras: Mapped[list["Obra"]] = relationship(back_populates="editora")

class Genero(Base):
    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria: Mapped[str] = mapped_column(String(50), unique=True)

    obras: Mapped[list["Obra"]] = relationship(
        secondary="obra_generos", back_populates="generos"
    )

class Obra(Base):
    __tablename__ = "obras"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(250))
    sinopse: Mapped[str | None] = mapped_column(Text)
    capa_url: Mapped[str | None] = mapped_column(String(250))
    tipo_obra: Mapped[TipoObra] = mapped_column(Enum(TipoObra))
    # unique evita salvar a mesma obra duas vezes
    api_url: Mapped[str] = mapped_column(String(250), unique=True)
    data_publicacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    editoras_id: Mapped[int | None] = mapped_column(ForeignKey("editoras.id"))

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

    @property
    def total_volumes(self) -> int:
        return len(self.volumes)

class Volume(Base):
    __tablename__ = "volumes"
    __table_args__ = (
        UniqueConstraint("obras_id", "numero_volume", name="uq_volumes_obra_numero"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo_volume: Mapped[str] = mapped_column(String(250))
    sinopse: Mapped[str | None] = mapped_column(Text)
    numero_volume: Mapped[int]
    capa_url: Mapped[str | None] = mapped_column(String(250))
    data_publicacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    obras_id: Mapped[int] = mapped_column(ForeignKey("obras.id", ondelete="CASCADE"))

    obra: Mapped["Obra"] = relationship(back_populates="volumes")
    usuarios: Mapped[list["UsuarioVolume"]] = relationship(
        back_populates="volume", cascade="all, delete-orphan"
    )

class Termo(Base):
    """Termos inadequados, usados para filtrar resenhas (moderação)."""
    __tablename__ = "termos"

    id: Mapped[int] = mapped_column(primary_key=True)
    termos_inadequados: Mapped[str] = mapped_column(String(100), unique=True)
