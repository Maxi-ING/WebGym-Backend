"""Seis tablas iniciales y catálogo de ejercicios.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("usuarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("correo", sa.String(255), nullable=False),
        sa.Column("clave_hash", sa.String(255), nullable=False),
        sa.Column("edad", sa.Integer),
        sa.Column("talla_m", sa.Numeric(4, 2)),
        sa.Column("objetivo", sa.String(240)),
        sa.CheckConstraint("edad IS NULL OR edad BETWEEN 18 AND 120", name="ck_usuario_edad"),
        sa.CheckConstraint("talla_m IS NULL OR talla_m BETWEEN 0.8 AND 2.5", name="ck_usuario_talla"))
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"], unique=True)
    op.create_table("ejercicios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("unidad", sa.String(10), nullable=False))
    op.create_table("mediciones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("peso_kg", sa.Numeric(6, 2), nullable=False),
        sa.CheckConstraint("peso_kg > 0", name="ck_medicion_peso"))
    op.create_index("ix_mediciones_usuario_fecha", "mediciones", ["usuario_id", "fecha"])
    op.create_table("sesiones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False))
    op.create_index("ix_sesiones_usuario_fecha", "sesiones", ["usuario_id", "fecha"])
    op.create_table("registros",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sesion_id", sa.Integer, sa.ForeignKey("sesiones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ejercicio_id", sa.Integer, sa.ForeignKey("ejercicios.id"), nullable=False),
        sa.Column("series", sa.Integer, nullable=False),
        sa.Column("repeticiones", sa.Integer, nullable=False),
        sa.Column("carga_kg", sa.Numeric(6, 2), nullable=False),
        sa.CheckConstraint("series BETWEEN 1 AND 50", name="ck_registro_series"),
        sa.CheckConstraint("repeticiones BETWEEN 1 AND 100", name="ck_registro_repeticiones"),
        sa.CheckConstraint("carga_kg >= 0", name="ck_registro_carga"))
    op.create_table("metas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ejercicio_id", sa.Integer, sa.ForeignKey("ejercicios.id"), nullable=False),
        sa.Column("carga_objetivo_kg", sa.Numeric(6, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.UniqueConstraint("usuario_id", "ejercicio_id", name="uq_meta_usuario_ejercicio"),
        sa.CheckConstraint("carga_objetivo_kg > 0", name="ck_meta_carga"),
        sa.CheckConstraint("estado IN ('activa','alcanzada')", name="ck_meta_estado"))
    op.bulk_insert(sa.table("ejercicios", sa.column("nombre", sa.String), sa.column("unidad", sa.String)), [
        {"nombre": "Sentadilla", "unidad": "kg"},
        {"nombre": "Press de banca", "unidad": "kg"},
        {"nombre": "Peso muerto", "unidad": "kg"},
        {"nombre": "Press militar", "unidad": "kg"},
        {"nombre": "Remo con barra", "unidad": "kg"},
    ])


def downgrade():
    for table in ("metas", "registros", "sesiones", "mediciones", "ejercicios", "usuarios"):
        op.drop_table(table)
