from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ejercicio, Meta, Registro, Sesion, Usuario
from app.schemas import MetaEntrada, SesionEntrada
from app.security import check_csrf, complete_user

router = APIRouter(prefix="/api", tags=["Entrenamiento"])


def serialize_session(row: Sesion) -> dict:
    return {"id": row.id, "fecha": row.fecha, "registros": [
        {"id": r.id, "ejercicio_id": r.ejercicio_id, "ejercicio": r.ejercicio.nombre,
         "series": r.series, "repeticiones": r.repeticiones, "carga_kg": float(r.carga_kg),
         "volumen_kg": float(r.series * r.repeticiones * r.carga_kg)}
        for r in sorted(row.registros, key=lambda r: r.id)
    ]}


@router.get("/ejercicios")
def exercises(db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    return [{"id": e.id, "nombre": e.nombre, "unidad": e.unidad} for e in db.scalars(select(Ejercicio).order_by(Ejercicio.nombre))]


@router.post("/sesiones", status_code=201, dependencies=[Depends(check_csrf)])
def create_session(payload: SesionEntrada, db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    ids = {r.ejercicio_id for r in payload.registros}
    exercises = db.scalars(select(Ejercicio).where(Ejercicio.id.in_(ids))).all()
    if len(exercises) != len(ids):
        raise HTTPException(422, "Hay ejercicios que no existen en el catálogo")
    row = Sesion(usuario_id=user.id, fecha=payload.fecha)
    row.registros = [Registro(ejercicio_id=r.ejercicio_id, series=r.series,
                              repeticiones=r.repeticiones, carga_kg=Decimal(str(r.carga_kg)))
                     for r in payload.registros]
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_session(row)


@router.get("/sesiones")
def sessions(db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    rows = db.scalars(select(Sesion).where(Sesion.usuario_id == user.id).order_by(Sesion.fecha.desc(), Sesion.id.desc())).all()
    return [serialize_session(row) for row in rows]


@router.delete("/sesiones/{session_id}", status_code=204, dependencies=[Depends(check_csrf)])
def delete_session(session_id: int, db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    row = db.scalar(select(Sesion).where(Sesion.id == session_id, Sesion.usuario_id == user.id))
    if row is None:
        raise HTTPException(404, "Sesión no encontrada")
    db.delete(row)
    db.commit()


@router.get("/metas")
def goals(db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    rows = db.scalars(select(Meta).where(Meta.usuario_id == user.id).order_by(Meta.id)).all()
    return [{"ejercicio_id": m.ejercicio_id, "ejercicio": m.ejercicio.nombre,
             "carga_objetivo_kg": float(m.carga_objetivo_kg), "estado": m.estado} for m in rows]


@router.put("/metas/{exercise_id}", dependencies=[Depends(check_csrf)])
def save_goal(exercise_id: int, payload: MetaEntrada, db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    exercise = db.get(Ejercicio, exercise_id)
    if exercise is None:
        raise HTTPException(404, "Ejercicio no encontrado")
    row = db.scalar(select(Meta).where(Meta.usuario_id == user.id, Meta.ejercicio_id == exercise_id))
    if row is None:
        row = Meta(usuario_id=user.id, ejercicio_id=exercise_id)
        db.add(row)
    row.carga_objetivo_kg = Decimal(str(payload.carga_objetivo_kg))
    row.estado = "activa"
    db.commit()
    return {"ejercicio_id": exercise_id, "carga_objetivo_kg": float(row.carga_objetivo_kg), "estado": row.estado}
