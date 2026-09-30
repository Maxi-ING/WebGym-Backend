from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario
from app.schemas import Ingreso, RegistroCuenta
from app.security import check_csrf, csrf_token, current_user, hasher
from app.services.indicators import AnalizadorProgreso

router = APIRouter(prefix="/api/auth", tags=["Acceso"])
indicators = AnalizadorProgreso()


@router.get("/csrf")
def csrf(request: Request):
    return {"csrf_token": csrf_token(request)}


@router.post("/registro", status_code=201, dependencies=[Depends(check_csrf)])
def register(payload: RegistroCuenta, request: Request, db: Session = Depends(get_db)):
    email = payload.correo.lower()
    if db.scalar(select(Usuario).where(Usuario.correo == email)):
        raise HTTPException(409, "Este correo ya está registrado")
    user = Usuario(nombre=payload.nombre.strip(), correo=email, clave_hash=hasher.hash(payload.clave))
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    request.session.clear()
    request.session["user_id"] = user.id
    return {"usuario": indicators.profile_data(user), "csrf_token": csrf_token(request)}


@router.post("/ingreso", dependencies=[Depends(check_csrf)])
def login(payload: Ingreso, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(Usuario).where(Usuario.correo == payload.correo.lower()))
    if user is None or not hasher.verify(payload.clave, user.clave_hash):
        raise HTTPException(401, "Credenciales inválidas")
    request.session.clear()
    request.session["user_id"] = user.id
    return {"usuario": indicators.profile_data(user), "csrf_token": csrf_token(request)}


@router.post("/salir", dependencies=[Depends(check_csrf)])
def logout(request: Request):
    request.session.clear()
    return {"mensaje": "Sesión cerrada"}


@router.get("/yo")
def me(user: Usuario = Depends(current_user)):
    return indicators.profile_data(user)
