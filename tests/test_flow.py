from datetime import date, timedelta

from conftest import profile, register, token


def test_registration_gate_training_and_analysis(client):
    csrf = register(client)
    assert client.get("/api/progreso").status_code == 409
    assert client.post("/api/sesiones", json={}).status_code == 403
    saved = profile(client, csrf)
    assert saved["imc"] == 26.1
    exercise_id = next(x["id"] for x in client.get("/api/ejercicios").json() if x["nombre"] == "Sentadilla")
    headers = {"X-CSRF-Token": csrf}
    assert client.put(f"/api/metas/{exercise_id}", headers=headers, json={"carga_objetivo_kg": 50}).status_code == 200
    assert client.post(f"/api/analisis/{exercise_id}", headers=headers).json()["estado"] == "datos_insuficientes"
    week = date.today() - timedelta(days=date.today().weekday())
    for idx, weight in enumerate(range(32, 48, 2)):
        day = week - timedelta(weeks=7 - idx)
        response = client.post("/api/sesiones", headers=headers, json={"fecha": day.isoformat(), "registros": [
            {"ejercicio_id": exercise_id, "series": 3, "repeticiones": 8, "carga_kg": weight}]})
        assert response.status_code == 201, response.text
    progress = client.get("/api/progreso").json()
    assert progress["sesiones_total"] == 8
    assert progress["volumen_total_kg"] == 3 * 8 * sum(range(32, 48, 2))
    assert "prediccion" not in progress
    analysis = client.post(f"/api/analisis/{exercise_id}", headers=headers).json()
    assert analysis["estado"] == "proyeccion"
    assert analysis["prediccion"]["pendiente_kg_semana"] == 2.0
    assert analysis["prediccion"]["carga_estimada_kg"] == 48.0
    assert analysis["prediccion"]["semanas_para_meta"] == 2


def test_data_isolation_and_invalid_values(client):
    first_csrf = register(client)
    profile(client, first_csrf)
    first = client.post("/api/sesiones", headers={"X-CSRF-Token": first_csrf}, json={
        "fecha": date.today().isoformat(), "registros": [{"ejercicio_id": 1,
        "series": 3, "repeticiones": 8, "carga_kg": 40}]})
    assert first.status_code == 201
    session_id = first.json()["id"]
    client.post("/api/auth/salir", headers={"X-CSRF-Token": first_csrf})
    second_csrf = register(client, "otra@example.com")
    profile(client, second_csrf)
    assert client.get("/api/sesiones").json() == []
    assert client.delete(f"/api/sesiones/{session_id}", headers={"X-CSRF-Token": second_csrf}).status_code == 404
    assert client.get("/api/progreso").json()["sesiones_total"] == 0
    invalid = client.post("/api/sesiones", headers={"X-CSRF-Token": second_csrf}, json={
        "fecha": date.today().isoformat(), "registros": [{"ejercicio_id": 1,
        "series": 0, "repeticiones": 8, "carga_kg": -2}]})
    assert invalid.status_code == 422
    assert client.get("/api/sesiones").json() == []


def test_invalid_login_and_duplicate_email(client):
    csrf = register(client)
    client.post("/api/auth/salir", headers={"X-CSRF-Token": csrf})
    csrf = token(client)
    bad = client.post("/api/auth/ingreso", headers={"X-CSRF-Token": csrf}, json={
        "correo": "ana@example.com", "clave": "Incorrecta"})
    assert bad.status_code == 401
    duplicate = client.post("/api/auth/registro", headers={"X-CSRF-Token": csrf}, json={
        "nombre": "Otra", "correo": "ana@example.com", "clave": "UnSecretoLargo123!"})
    assert duplicate.status_code == 409
    assert client.get("/api/auth/yo").status_code == 401
