import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://eventhub:changez-moi-en-mot-de-passe-fort@localhost:5432/eventhub_registrations",
)
EVENTS_SERVICE_URL = os.getenv("EVENTS_SERVICE_URL", "http://localhost:8001")
PARTICIPANTS_SERVICE_URL = os.getenv("PARTICIPANTS_SERVICE_URL", "http://localhost:8002")
SERVICE_NAME = os.getenv("SERVICE_NAME", "registrations-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
