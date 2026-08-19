import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.routing import APIRoute
from sqlalchemy import text

from app import config
from app.database import Base, engine
from app.routes import router

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(config.SERVICE_NAME)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Nomme chaque opération d'après le nom de la fonction Python.

    Sans cela, FastAPI génère des identifiants du type
    « list_events_api_events_get », et openapi-generator produit des
    méthodes TypeScript illisibles (listEventsApiEventsGet).
    Avec, on obtient simplement listEvents().
    """
    return route.name


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Crée les tables AU DÉMARRAGE, pas à l'import du module.

    C'est important : si create_all() est appelé au niveau du module, il
    tente de joindre PostgreSQL dès qu'on fait « import app.main » — donc
    aussi pendant les tests unitaires et la collecte pytest, qui échouent
    alors en CI faute de base. En production on utiliserait Alembic.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("%s started", config.SERVICE_NAME)
    yield


app = FastAPI(
    title="Events Service",
    description="Microservice de gestion des événements du DIT",
    version="1.0.0",
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
)

# Le préfixe /api est porté par le service lui-même : l'URL appelée par le
# navigateur est exactement celle que reçoit le service, la gateway ne
# réécrit rien. Cela rend le débogage beaucoup plus simple.
app.include_router(router, prefix="/api/events", tags=["events"])


@app.get("/health", tags=["health"])
def health():
    """Liveness : le processus répond. Utilisé par le HEALTHCHECK Docker."""
    return {"status": "ok", "service": config.SERVICE_NAME}


@app.get("/health/ready", tags=["health"])
def readiness(response: Response):
    """Readiness : le service ET sa base de données répondent."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as exc:  # noqa: BLE001
        logger.error("database unreachable: %s", exc)
        db_status = "down"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if db_status == "up" else "degraded",
        "service": config.SERVICE_NAME,
        "components": {"database": db_status},
    }
