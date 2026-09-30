from decimal import Decimal

from app.models import Usuario


class AnalizadorProgreso:
    """Calcula indicadores individuales sin modificar los registros."""

    @staticmethod
    def bmi(peso_kg: Decimal, talla_m: Decimal) -> float:
        return round(float(peso_kg / (talla_m * talla_m)), 1)

    def profile_data(self, user: Usuario) -> dict:
        last = max(user.mediciones, key=lambda m: (m.fecha, m.id), default=None)
        complete = user.edad is not None and user.talla_m is not None and last is not None and bool(user.objetivo)
        return {
            "id": user.id, "nombre": user.nombre, "correo": user.correo,
            "perfil_completo": complete, "edad": user.edad,
            "talla_m": float(user.talla_m) if user.talla_m is not None else None,
            "objetivo": user.objetivo,
            "peso_kg": float(last.peso_kg) if last else None,
            "imc": self.bmi(last.peso_kg, user.talla_m) if complete else None,
        }

    def progress_data(self, user: Usuario) -> dict:
        measurements = sorted(user.mediciones, key=lambda m: (m.fecha, m.id))
        sessions = sorted(user.sesiones, key=lambda s: (s.fecha, s.id))
        by_exercise: dict[int, dict] = {}
        total_volume = Decimal("0")
        for session in sessions:
            for record in session.registros:
                vol = record.series * record.repeticiones * record.carga_kg
                total_volume += vol
                bucket = by_exercise.setdefault(record.ejercicio_id, {
                    "ejercicio_id": record.ejercicio_id, "nombre": record.ejercicio.nombre,
                    "puntos": [],
                })
                bucket["puntos"].append({
                    "fecha": session.fecha.isoformat(), "carga_kg": float(record.carga_kg),
                    "volumen_kg": float(vol),
                })
        return {
            "perfil": self.profile_data(user), "sesiones_total": len(sessions),
            "volumen_total_kg": float(total_volume),
            "mediciones": [{"fecha": m.fecha.isoformat(), "peso_kg": float(m.peso_kg)} for m in measurements],
            "ejercicios": list(sorted(by_exercise.values(), key=lambda row: row["nombre"])),
        }
