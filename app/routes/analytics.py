from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ejercicio, Meta, Usuario
from app.security import check_csrf, complete_user
from app.services.indicators import AnalizadorProgreso
from app.services.predictor import PredictorMeta

router = APIRouter(prefix="/api", tags=["Progreso y análisis"])
indicators = AnalizadorProgreso()
predictor = PredictorMeta()


@router.get("/progreso")
def progress(user: Usuario = Depends(complete_user)):
    return indicators.progress_data(user)


@router.post("/analisis/{exercise_id}", dependencies=[Depends(check_csrf)])
def run_analysis(exercise_id: int, db: Session = Depends(get_db), user: Usuario = Depends(complete_user)):
    exercise = db.get(Ejercicio, exercise_id)
    if exercise is None:
        raise HTTPException(404, "Ejercicio no encontrado")
    goal = db.scalar(select(Meta).where(Meta.usuario_id == user.id, Meta.ejercicio_id == exercise_id))
    result = predictor.analyze(user.sesiones, exercise_id, float(goal.carga_objetivo_kg) if goal else None)
    return {"ejercicio": exercise.nombre, **result}
