from datetime import date, timedelta
from decimal import Decimal

from app.models import Registro, Sesion
from app.services.predictor import PredictorMeta


def sessions_for(weights):
    monday = date(2026, 1, 5)
    result = []
    for index, weight in enumerate(weights):
        session = Sesion(fecha=monday + timedelta(weeks=index))
        session.registros = [Registro(ejercicio_id=1, series=3, repeticiones=8, carga_kg=Decimal(weight))]
        result.append(session)
    return result


def test_no_projection_for_short_or_flat_history():
    predictor = PredictorMeta()
    assert predictor.analyze(sessions_for([32, 34, 36]), 1, 50)["estado"] == "datos_insuficientes"
    flat = predictor.analyze(sessions_for([40, 40, 40, 40]), 1, 50)
    assert flat["estado"] == "tendencia_no_positiva"
    assert flat["prediccion"] is None


def test_four_points_preliminary_and_weekly_maximum():
    history = sessions_for([32, 34, 36, 38])
    another = Sesion(fecha=date(2026, 1, 8))
    another.registros = [Registro(ejercicio_id=1, series=3, repeticiones=8, carga_kg=Decimal(30))]
    history.append(another)
    result = PredictorMeta().analyze(history, 1, 50)
    assert result["semanas_registradas"] == 4
    assert result["historial"][0]["carga_kg"] == 32
    assert result["prediccion"]["preliminar"] is True
