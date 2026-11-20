# Mi entrega de la semana 15: Docker y contenedorización

Empaqueté la API acumulada con una imagen multi-stage, usuario sin privilegios, migraciones automáticas y health checks. Uso Compose para API, PostgreSQL y Redis y un perfil test separado. Mantengo volúmenes para base de datos, Redis y uploads.

## Cómo la ejecuto

Uso Python 3.12, PostgreSQL 17 y Redis 7. Copio .env.example a .env y configuro mis valores antes de iniciar.

```powershell
uv sync
Copy-Item .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Las migraciones crean el esquema desde una base vacía. No necesito archivos de otra semana ni marcar un baseline manualmente. Abro http://127.0.0.1:8000/docs y uso el login OAuth2 con formulario en /api/v1/auth/token.

## Cómo organicé mi API

Creo mi primer administrador con `uv run python -m scripts.seed_admin`, después de configurar SEED_ADMIN_PASSWORD (mínimo 12 caracteres), SEED_ADMIN_USERNAME y SEED_ADMIN_EMAIL en el entorno. El script rechaza usuarios existentes para evitar cambiar credenciales por accidente.

Recibo y valido HTTP en routers, aplico reglas de negocio en servicios y consulto PostgreSQL desde repositorios asíncronos. Uso modelos Pydantic distintos para entradas y respuestas y oculto hashes y datos internos. Centralizo configuración y errores.

| Recurso | Rutas |
|---|---|
| Identidad | /api/v1/auth/register, token, refresh, logout, me |
| Usuarios | /api/v1/users y /api/v1/users/{id}, solo admin |
| Posts | /api/v1/posts, /{id}, /{id}/image y /export |
| Comentarios | /api/v1/posts/{id}/comments y /api/v1/comments/{id} |
| Categorías | /api/v1/categories |
| Notificaciones | /api/v1/notifications y /{id}/read |
| Autoguardado | /api/v1/autosave |
| Tiempo real | /api/v1/ws/notifications y /api/v1/ws/client |
| Estado | / y /health |

El registro crea un usuario con rol user. Para publicar necesito editor o admin. Restrinjo la edición al propietario o admin. Consulto notificaciones propias y respondo 404 cuando una notificación pertenece a otra persona.

## Redis y persistencia

Guardo posts públicos por 300 segundos, listas anónimas por 60 y usuarios por 600. Uso jitter, lock y SCAN para invalidación. El autoguardado dura un día. Aplico 30 peticiones por minuto por usuario o IP, y 5 por minuto por IP en login. Si Redis falla, continúo con PostgreSQL y marco el estado como degraded; el autoguardado devuelve 503.

Los datos de negocio y refresh tokens viven en PostgreSQL. Las conexiones WebSocket viven por proceso y se comunican entre workers a través de pub/sub. Mis tareas de email son una simulación en var/outbox.log; no las trato como una cola durable.

## Cómo verifico mi trabajo

Ejecuto `uv run python -m scripts.smoke` contra una base de prueba preparada y con límites elevados para recorrer registro, login, roles, CRUD, caché, autoguardado y notificaciones. Reviso también VERIFICACION.md.

Agregué /api/v1/tags, /api/v1/users/me, /api/v1/users/me/posts y /api/v1/ws/posts/{post_id}. Uso el perfil para editar mi email sin permitir que una entrada pública cambie mi rol.

En CHECKPOINT.md registré mis hallazgos y en RETROSPECTIVA.md dejé mi reflexión 4Ls. Verifico estilo con `ruff check app` y `ruff format --check app`.

Mi suite tiene 62 pruebas separadas en unit, integration y e2e. En Python 3.12 medí 90,27 % de cobertura total. El reporte coverage.xml conserva la medición. Ejecuto `uv run pytest --cov` o `uv run pytest -m unit`. Para integración uso TEST_DATABASE_URL con una base cuyo nombre contiene test y TEST_REDIS_URL en la DB 15 de Redis. Las fixtures limpian únicamente ese entorno de prueba.

## Cómo uso Docker

Configuro POSTGRES_PASSWORD y JWT_SECRET en .env. Ejecuto:

```powershell
docker compose up -d --build --wait
docker compose ps
docker compose --profile test run --build --rm tests
docker compose exec api whoami
```

La API queda en http://127.0.0.1:8000/docs. PostgreSQL y Redis quedan dentro de la red de Compose. La imagen de producción pesa 283,5 MB y corre como appuser. El entrypoint aplica Alembic antes de iniciar Uvicorn. Puedo detener con `docker compose down` y volver a iniciar conservando los volúmenes. Los tests usan pulse_test y Redis DB 15, separados de pulse_blog y Redis DB 0.
