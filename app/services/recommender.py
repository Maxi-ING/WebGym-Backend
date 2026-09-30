class Recomendador:
    """Convierte el resultado estadístico en un mensaje de reglas explicables."""

    @staticmethod
    def insufficient_data() -> str:
        return "Registra cargas en al menos cuatro semanas distintas para obtener una proyección."

    def suggest(self, *, state: str, weeks: int, recent_active: int, distant_goal: bool) -> str:
        messages = {
            "meta_alcanzada": "Ya registraste una carga igual o superior a tu meta. Revísala antes de fijar una nueva.",
            "tendencia_no_positiva": "La carga se ha estabilizado o reducido. Revisa tus registros y conversa con tu entrenador.",
            "proyeccion": "Tu carga muestra una tendencia ascendente. La proyección es orientativa; el avance real puede variar.",
        }
        message = messages[state]
        if distant_goal:
            message = "Al ritmo observado, la meta está lejana. Revisa si el plazo propuesto es realista."
        if weeks == 4:
            message += " Resultado preliminar: solo hay cuatro semanas registradas."
        if recent_active < 2:
            message += " Hay pocos registros en las cuatro semanas finales; registra sesiones con regularidad para evaluar mejor la tendencia."
        return message
