import hmac
import secrets

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario

hasher = PasswordHash.recommended()


def csrf_token(request: Request) -> str:
    if "csrf" not in request.session:
        request.session["csrf"] = secrets.token_urlsafe(32)
    return request.session["csrf"]


def check_csrf(request: Request) -> None:
    expected = request.session.get("csrf", "")
    received = request.headers.get("x-csrf-token", "")
    if not expected or not hmac.compare_digest(expected, received):
        raise HTTPException(403, "Token CSRF inválido")


def current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    user_id = request.session.get("user_id")
    user = db.get(Usuario, user_id) if isinstance(user_id, int) else None
    if user is None:
        raise HTTPException(401, "Inicia sesión")
    return user


def complete_user(user: Usuario = Depends(current_user)) -> Usuario:
    if user.edad is None or user.talla_m is None or not user.mediciones or not user.objetivo:
        raise HTTPException(409, "Completa primero los datos iniciales del perfil")
    return user
