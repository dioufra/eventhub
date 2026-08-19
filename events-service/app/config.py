import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://eventhub:changez-moi-en-mot-de-passe-fort@localhost:5432/eventhub_events",
)
SERVICE_NAME = os.getenv("SERVICE_NAME", "events-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
