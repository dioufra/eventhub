from fastapi import FastAPI
from app.database import Base, engine
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Registrations Service",
    description="Microservice de gestion des inscriptions à des événements",
    version="1.0.0",
)

app.include_router(router, prefix="/registrations", tags=["registrations"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "registrations-service"}
