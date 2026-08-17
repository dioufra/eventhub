import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from app import config
from app.database import Base, engine
from app.routes import router

logging.basicConfig(
    level=getattr(config, "LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(config.SERVICE_NAME)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Crée les tables AU DÉMARRAGE, pas à l'import du module.

    Si create_all() est appelé au niveau du module, il tente de joindre
    PostgreSQL dès « import app.main » — donc aussi pendant la collecte
    pytest, qui échoue alors en CI faute de base disponible.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("%s started", config.SERVICE_NAME)
    yield


app = FastAPI(
    title="Registrations Service",
    description="Microservice de gestion des inscriptions à des événements",
    version="1.0.0",
    lifespan=lifespan,
)

# La gateway route /api/registrations : le service doit répondre sur ce
# préfixe exact. L'URL vue par le navigateur est celle vue par le service.
app.include_router(router, prefix="/api/registrations", tags=["registrations"])


@app.get("/health", tags=["health"])
def health():
    """Liveness : utilisé par le HEALTHCHECK Docker."""
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
