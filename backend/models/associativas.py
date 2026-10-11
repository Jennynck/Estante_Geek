from datetime import datetime
from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey, String, Table,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, StatusLeitura, valores_enum

# N:N entre obras e gêneros
obra_generos = Table(
    "obra_generos",
    Base.metadata,
    Column("obras_id", ForeignKey("obras.id", ondelete="CASCADE"), primary_key=True),
    Column("generos_id", ForeignKey("generos.id", ondelete="CASCADE"), primary_key=True),
)

class UsuarioObra(Base):
    """Obra na estante do usuário (com status, nota e resenha)."""
    __tablename__ = "usuarios_obras"
    __table_args__ = (
        UniqueConstraint("usuarios_id", "obras_id", name="uq_usuarios_obras"),
        CheckConstraint("nota >= 1 AND nota <= 10", name="ck_usuarios_obras_nota"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nota: Mapped[int | None]
    resenha: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[StatusLeitura] = mapped_column(
        Enum(StatusLeitura, native_enum=False, create_constraint=True,
             values_callable=valores_enum),
        default=StatusLeitura.QUERO_LER,
    )
    data_publicacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    usuarios_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    obras_id: Mapped[int] = mapped_column(ForeignKey("obras.id", ondelete="CASCADE"))

    usuario: Mapped["Usuario"] = relationship(back_populates="obras")
    obra: Mapped["Obra"] = relationship(back_populates="usuarios")

class UsuarioVolume(Base):
    """Situação de cada volume para o usuário (possui? já leu?)."""
    __tablename__ = "usuario_volumes"
    __table_args__ = (
        UniqueConstraint("usuarios_id", "volumes_id", name="uq_usuario_volumes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    possui_volume: Mapped[bool] = mapped_column(Boolean, default=False)
    status_leitura: Mapped[StatusLeitura] = mapped_column(
        Enum(StatusLeitura, native_enum=False, create_constraint=True,
             values_callable=valores_enum),
        default=StatusLeitura.QUERO_LER,
    )
    usuarios_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    volumes_id: Mapped[int] = mapped_column(ForeignKey("volumes.id", ondelete="CASCADE"))

    usuario: Mapped["Usuario"] = relationship(back_populates="volumes")
    volume: Mapped["Volume"] = relationship(back_populates="usuarios")
