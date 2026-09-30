from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    clave_hash: Mapped[str] = mapped_column(String(255))
    edad: Mapped[int | None] = mapped_column(nullable=True)
    talla_m: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    objetivo: Mapped[str | None] = mapped_column(String(240), nullable=True)
    mediciones: Mapped[list["Medicion"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    metas: Mapped[list["Meta"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("edad IS NULL OR edad BETWEEN 18 AND 120", name="ck_usuario_edad"),
        CheckConstraint("talla_m IS NULL OR talla_m BETWEEN 0.8 AND 2.5", name="ck_usuario_talla"),
    )


class Medicion(Base):
    __tablename__ = "mediciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    usuario: Mapped[Usuario] = relationship(back_populates="mediciones")
    __table_args__ = (CheckConstraint("peso_kg > 0", name="ck_medicion_peso"), Index("ix_mediciones_usuario_fecha", "usuario_id", "fecha"))


class Ejercicio(Base):
    __tablename__ = "ejercicios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    unidad: Mapped[str] = mapped_column(String(10), default="kg")


class Sesion(Base):
    __tablename__ = "sesiones"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    usuario: Mapped[Usuario] = relationship(back_populates="sesiones")
    registros: Mapped[list["Registro"]] = relationship(back_populates="sesion", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_sesiones_usuario_fecha", "usuario_id", "fecha"),)


class Registro(Base):
    __tablename__ = "registros"
    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_id: Mapped[int] = mapped_column(ForeignKey("sesiones.id", ondelete="CASCADE"))
    ejercicio_id: Mapped[int] = mapped_column(ForeignKey("ejercicios.id"))
    series: Mapped[int]
    repeticiones: Mapped[int]
    carga_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    sesion: Mapped[Sesion] = relationship(back_populates="registros")
    ejercicio: Mapped[Ejercicio] = relationship()
    __table_args__ = (
        CheckConstraint("series BETWEEN 1 AND 50", name="ck_registro_series"),
        CheckConstraint("repeticiones BETWEEN 1 AND 100", name="ck_registro_repeticiones"),
        CheckConstraint("carga_kg >= 0", name="ck_registro_carga"),
    )


class Meta(Base):
    __tablename__ = "metas"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    ejercicio_id: Mapped[int] = mapped_column(ForeignKey("ejercicios.id"))
    carga_objetivo_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    estado: Mapped[str] = mapped_column(String(20), default="activa")
    usuario: Mapped[Usuario] = relationship(back_populates="metas")
    ejercicio: Mapped[Ejercicio] = relationship()
    __table_args__ = (
        UniqueConstraint("usuario_id", "ejercicio_id", name="uq_meta_usuario_ejercicio"),
        CheckConstraint("carga_objetivo_kg > 0", name="ck_meta_carga"),
        CheckConstraint("estado IN ('activa','alcanzada')", name="ck_meta_estado"),
    )
