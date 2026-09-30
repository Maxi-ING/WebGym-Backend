# FitAnalytics AI — backend

Backend funcional de la primera etapa. Expone una API JSON documentada en `/docs` para conectar después las páginas del prototipo. La parte visual aún no forma parte de esta entrega.

## Requisitos

- Python 3.12 recomendado.
- PostgreSQL para el despliegue en Render. Para pruebas locales rápidas se admite SQLite.

## Instalar en Windows (PowerShell)

```powershell
cd WebGym-Backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Si PowerShell impide activar el entorno, usa `.venv\Scripts\python.exe` en lugar de `python` en los comandos posteriores.

## Instalar en Linux o macOS

```bash
cd WebGym-Backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

En `.env`, configura `DATABASE_URL` y una `SESSION_SECRET` aleatoria de al menos 32 caracteres. Para empezar sin un servidor PostgreSQL, cambia `DATABASE_URL` a `sqlite:///./fitanalytics.db`. Nunca subas `.env` a GitHub. `COOKIE_SECURE=false` solo sirve para HTTP local; en Render usa `true`.

## Iniciar

Desde la carpeta raíz del backend, con el entorno activado:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000/docs>. La ruta `GET /api/salud` confirma que la base responde. Cada cambio de esquema se aplica con `alembic upgrade head`; el servidor no crea tablas automáticamente.

## Cuenta demo opcional

Después de migrar, define `DEMO_PASSWORD` con al menos 12 caracteres y ejecuta:

```bash
python -m scripts.seed_demo
```

Esto crea `demo@fitanalytics.local`, ocho semanas ficticias de sentadilla y una meta de 50 kg. Es un comando explícito: las cuentas nuevas no heredan esos registros. La segunda ejecución se detiene sin duplicar datos. No uses una contraseña demo pública en un despliegue abierto.

## Orden de llamadas de la futura interfaz

1. `GET /api/auth/csrf` entrega `csrf_token` y una cookie de sesión.
2. En `POST /api/auth/registro` o `POST /api/auth/ingreso`, envía `X-CSRF-Token` con ese valor. Conserva la nueva cookie y el **nuevo** `csrf_token` devuelto al autenticar.
3. `GET /api/auth/yo` entrega `perfil_completo`. Si es `false`, abre el modal y guarda edad, talla en metros, peso en kg y objetivo con `PUT /api/perfil/datos`.
4. Consulta `GET /api/ejercicios`, registra sesiones con `POST /api/sesiones`, mediciones con `POST /api/perfil/mediciones` y metas con `PUT /api/metas/{ejercicio_id}`.
5. `GET /api/progreso` devuelve solo indicadores históricos para los gráficos descriptivos.
6. Cuando la persona pulse **Analizar mi progreso**, llama `POST /api/analisis/{ejercicio_id}`. Solo esa ruta ajusta `LinearRegression` al historial del usuario.

Todas las rutas que modifican datos requieren la cabecera `X-CSRF-Token`; las rutas privadas requieren la cookie de sesión. Desde el navegador, `fetch` en el mismo origen incluye la cookie de forma predeterminada. La documentación interactiva `/docs` sirve para inspeccionar contratos, pero para probar las rutas privadas resulta más cómodo un cliente que conserve cookies y permita establecer la cabecera CSRF.

Ejemplo Python tras iniciar el servidor:

```python
import requests

with requests.Session() as client:
    csrf = client.get("http://127.0.0.1:8000/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "http://127.0.0.1:8000/api/auth/registro",
        headers={"X-CSRF-Token": csrf},
        json={"nombre": "Ana", "correo": "ana@example.com", "clave": "ClaveLarga12345!"},
    )
    response.raise_for_status()
    csrf = response.json()["csrf_token"]
    response = client.put(
        "http://127.0.0.1:8000/api/perfil/datos",
        headers={"X-CSRF-Token": csrf},
        json={"edad": 25, "talla_m": 1.75, "peso_kg": 80, "objetivo": "Mejorar fuerza"},
    )
    print(response.json())
```

Para este ejemplo instala `requests` aparte (`python -m pip install requests`) o usa cualquier cliente HTTP. `requests` no es dependencia del backend.

## Análisis y límites

El modelo usa la carga máxima por semana calendario de un ejercicio. Con menos de cuatro semanas distintas devuelve `datos_insuficientes`. Con tendencia no positiva o meta ya alcanzada no devuelve proyección. Con cuatro o cinco puntos marca la proyección como preliminar; desde seis calcula el error de la última semana como comprobación ilustrativa. El gráfico posterior podrá unir `historial` con `prediccion`. Las recomendaciones son reglas simples y no son consejo médico ni garantizan una fecha de logro.

## Pruebas

```bash
python -m pytest -q
```

Incluyen autenticación, modal inicial, validación, aislamiento entre usuarios, cálculo de IMC/volumen, mínimo de semanas, tendencia estancada y ejemplo de proyección de 32 a 46 kg.
GitHub Actions también ejecuta estas pruebas y verifica la migración y el acceso de la cuenta demo contra PostgreSQL en cada envío a `dev`, `realize` y `main`.

## Despliegue previsto en Render

1. Conecta este repositorio de GitHub como Web Service; la raíz del proyecto es la raíz del repositorio.
2. Crea una base de datos Render Postgres y un Web Service Python en la misma región. Conecta el servicio al repositorio.
3. En el servicio configura `DATABASE_URL` con la URL **interna** de PostgreSQL, `SESSION_SECRET` con una cadena segura y `COOKIE_SECURE=true`.
4. Build command: `pip install -r requirements.txt`.
5. Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Verifica `/api/salud`, el registro y el análisis con una cuenta de prueba. Puedes activar el despliegue automático en cada cambio de la rama principal.

No publiques la URL de la base de datos ni la clave de sesión. Para esta entrega de backend las páginas Jinja2/Chart.js se construirán en la siguiente etapa, usando el mismo origen y repositorio.

## Organización

- `app/models.py`: seis tablas ORM.
- `app/routes/`: acceso, perfil, entrenamiento y análisis.
- `app/services/`: clases `AnalizadorProgreso`, `PredictorMeta` y `Recomendador`.
- `migrations/`: versión inicial de la base y catálogo.
- `scripts/seed_demo.py`: datos sintéticos opcionales.
- `tests/`: pruebas automatizadas del flujo.
