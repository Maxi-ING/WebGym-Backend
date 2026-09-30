from datetime import date, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression

from app.models import Sesion
from app.services.recommender import Recomendador


class PredictorMeta:
    """Ajusta un modelo para un usuario y ejercicio solo cuando se solicita."""

    def __init__(self, recommender: Recomendador | None = None):
        self.recommender = recommender or Recomendador()

    @staticmethod
    def week_start(day: date) -> date:
        return day - timedelta(days=day.weekday())

    def weekly_max(self, sessions: list[Sesion], exercise_id: int) -> list[tuple[date, float]]:
        maximum: dict[date, float] = {}
        for session in sessions:
            for record in session.registros:
                if record.ejercicio_id == exercise_id:
                    week = self.week_start(session.fecha)
                    maximum[week] = max(maximum.get(week, 0), float(record.carga_kg))
        return sorted(maximum.items())

    def analyze(self, sessions: list[Sesion], exercise_id: int, target: float | None) -> dict:
        points = self.weekly_max(sessions, exercise_id)
        history = [{"semana": day.isoformat(), "carga_kg": load} for day, load in points]
        common = {"ejercicio_id": exercise_id, "historial": history, "semanas_registradas": len(points)}
        if len(points) < 4:
            return {**common, "estado": "datos_insuficientes", "prediccion": None,
                    "mensaje": self.recommender.insufficient_data()}

        origin = points[0][0]
        x = np.array([(day - origin).days / 7 for day, _ in points], dtype=float).reshape(-1, 1)
        y = np.array([load for _, load in points], dtype=float)
        model = LinearRegression().fit(x, y)
        slope = float(model.coef_[0])
        latest_week, latest_load = points[-1]
        next_week = latest_week + timedelta(weeks=1)
        next_x = np.array([[(next_week - origin).days / 7]])
        next_load = max(0.0, float(model.predict(next_x)[0]))

        # Una semana reservada ilustra el error; no acredita precisión general.
        error = None
        if len(points) >= 6:
            check = LinearRegression().fit(x[:-1], y[:-1])
            error = round(abs(float(check.predict(x[-1:])[0]) - y[-1]), 2)

        prediction = {
            "pendiente_kg_semana": round(slope, 2),
            "proxima_semana": next_week.isoformat(),
            "carga_estimada_kg": round(next_load, 2),
            "error_ultima_semana_kg": error,
            "preliminar": len(points) < 6,
            "meta_kg": target,
            "semanas_para_meta": None,
            "semana_meta_estimada": None,
        }
        if target is not None and latest_load >= target:
            state = "meta_alcanzada"
            prediction = None
        elif slope <= 0:
            state = "tendencia_no_positiva"
            prediction = None
        else:
            state = "proyeccion"
            if target is not None:
                target_x = (target - float(model.intercept_)) / slope
                weeks = max(1, int(np.ceil(target_x - x[-1][0])))
                if weeks <= 52:
                    prediction["semanas_para_meta"] = weeks
                    prediction["semana_meta_estimada"] = (latest_week + timedelta(weeks=weeks)).isoformat()

        recent_active = sum(1 for day, _ in points if day >= latest_week - timedelta(weeks=3))
        message = self.recommender.suggest(
            state=state, weeks=len(points), recent_active=recent_active,
            distant_goal=state == "proyeccion" and target is not None
                         and prediction["semanas_para_meta"] is None,
        )
        return {**common, "estado": state, "pendiente_kg_semana": round(slope, 2),
                "semanas_activas_ultimas_4": recent_active,
                "prediccion": prediction, "mensaje": message}
