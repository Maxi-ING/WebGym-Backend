"""Crea una cuenta demo con datos sintéticos solo tras una orden explícita."""
import os
from datetime import date, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

load_dotenv()

from app.db import engine  # noqa: E402
from app.models import Ejercicio, Medicion, Meta, Registro, Sesion, Usuario  # noqa: E402
from app.security import hasher  # noqa: E402


def seed():
    password = os.getenv("DEMO_PASSWORD", "")
    if len(password) < 12:
        raise SystemExit("Define DEMO_PASSWORD con al menos 12 caracteres")
    with Session(engine()) as db:
        if db.scalar(select(Usuario).where(Usuario.correo == "demo@fitanalytics.local")):
            raise SystemExit("La cuenta demo ya existe; no se duplicaron datos")
        exercise = db.scalar(select(Ejercicio).where(Ejercicio.nombre == "Sentadilla"))
        if exercise is None:
            raise SystemExit("Ejecuta primero: alembic upgrade head")
        user = Usuario(nombre="Cuenta demostración", correo="demo@fitanalytics.local",
                       clave_hash=hasher.hash(password), edad=25, talla_m=Decimal("1.75"),
                       objetivo="Mejorar mi fuerza en sentadilla")
        db.add(user)
        db.flush()
        today = date.today()
        db.add(Medicion(usuario_id=user.id, fecha=today, peso_kg=Decimal("80")))
        db.add(Meta(usuario_id=user.id, ejercicio_id=exercise.id,
                    carga_objetivo_kg=Decimal("50"), estado="activa"))
        current_week = today - timedelta(days=today.weekday())
        for index, weight in enumerate(range(32, 48, 2)):
            day = current_week - timedelta(weeks=7-index)
            session = Sesion(usuario_id=user.id, fecha=day)
            session.registros.append(Registro(ejercicio_id=exercise.id, series=3,
                                               repeticiones=8, carga_kg=Decimal(weight)))
            db.add(session)
        db.commit()
    print("Cuenta demo creada: demo@fitanalytics.local; ocho semanas de datos sintéticos")


if __name__ == "__main__":
    seed()
