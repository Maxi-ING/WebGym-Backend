from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Medicion, Usuario
from app.schemas import MedicionEntrada, PerfilEntrada
from app.security import check_csrf, complete_user, current_user
from app.services.indicators import AnalizadorProgreso

router = APIRouter(prefix="/api/perfil", tags=["Perfil"])
indicators = AnalizadorProgreso()


@router.get("")
def profile(user: Usuario = Depends(current_user)):
    return indicators.profile_data(user)


@router.put("/datos", dependencies=[Depends(check_csrf)])
def save_profile(payload: PerfilEntrada, db: Session = Depends(get_db), user: Usuario = Depends(current_user)):
    user.edad = payload.edad
    user.talla_m = Decimal(str(payload.talla_m))
    user.objetivo = payload.objetivo.strip()
    # Editing the profile on the same day updates the daily measurement.
    today = date.today()
    measurement = db.scalar(select(Medicion).where(Medicion.usuario_id == user.id, Medicion.fecha == today).order_by(Medicion.id.desc()))
    if measurement is None:
        measurement = Medicion(usuario_id=user.id, fecha=today, peso_kg=Decimal(str(payload.peso_kg)))
        db.add(measurement)
    else:
        measurement.peso_kg = Decimal(str(payload.peso_kg))
    db.commit()
    db.refresh(user)
    return indicators.profile_data(user)


@router.get("/mediciones")
def measurements(db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    rows = db.scalars(select(Medicion).where(Medicion.usuario_id == user.id).order_by(Medicion.fecha, Medicion.id)).all()
    return [{"id": row.id, "fecha": row.fecha, "peso_kg": float(row.peso_kg)} for row in rows]


@router.post("/mediciones", status_code=201, dependencies=[Depends(check_csrf)])
def add_measurement(payload: MedicionEntrada, db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    row = Medicion(usuario_id=user.id, fecha=payload.fecha, peso_kg=Decimal(str(payload.peso_kg)))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "fecha": row.fecha, "peso_kg": float(row.peso_kg)}
