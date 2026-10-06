from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, StatusLeitura

# N:N entre obras e gêneros (sem atributos extras)
obra_generos = Table(
    "obra_generos",
    Base.metadata,
    Column("obras_id", ForeignKey("obras.id", ondelete="CASCADE"), primary_key=True),
    Column("generos_id", ForeignKey("generos.id", ondelete="CASCADE"), primary_key=True),
)

class UsuarioObra(Base):
    """Obra na estante do usuário (com nota e resenha)."""
    __tablename__ = "usuarios_obras"
    __table_args__ = (
        UniqueConstraint("usuarios_id", "obras_id", name="uq_usuarios_obras"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuarios_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    obras_id: Mapped[int] = mapped_column(ForeignKey("obras.id", ondelete="CASCADE"))
    status: Mapped[StatusLeitura | None] = mapped_column(Enum(StatusLeitura))
    nota: Mapped[int | None]
    resenha: Mapped[str | None] = mapped_column(Text)
    data_resenha: Mapped[datetime | None] = mapped_column(DateTime)
    adicionada_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    usuario: Mapped["Usuario"] = relationship(back_populates="obras")
    obra: Mapped["Obra"] = relationship(back_populates="usuarios")

class UsuarioVolume(Base):
    """Situação de cada volume para o usuário (possui? já leu?)."""
    __tablename__ = "usuario_volumes"
    __table_args__ = (
        UniqueConstraint("usuarios_id", "volumes_id", name="uq_usuario_volumes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuarios_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    volumes_id: Mapped[int] = mapped_column(ForeignKey("volumes.id", ondelete="CASCADE"))
    possui_volume: Mapped[bool] = mapped_column(Boolean, default=False)
    status_leitura: Mapped[StatusLeitura] = mapped_column(
        Enum(StatusLeitura), default=StatusLeitura.QUERO_LER
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="volumes")
    volume: Mapped["Volume"] = relationship(back_populates="usuarios")