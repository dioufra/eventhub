# =============================================================================
#  registrations-service — image de production
#
#  Alpine suffit ici : pg8000 est un driver PostgreSQL 100 % Python, il ne
#  demande aucune compilation (contrairement à psycopg2, qui exigerait gcc
#  et les en-têtes libpq, soit ~200 Mo de plus).
# =============================================================================
FROM python:3.12-alpine

# PYTHONDONTWRITEBYTECODE : pas de .pyc, inutiles en conteneur
# PYTHONUNBUFFERED       : logs immédiats, sinon « docker logs » est en retard
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copié seul, AVANT le code : couche mise en cache, reconstruite
# uniquement si requirements.txt change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Utilisateur non privilégié : si l'application est compromise,
# l'attaquant n'est pas root dans le conteneur.
RUN adduser -D -u 1001 appuser

# Le code en dernier : c'est ce qui change le plus souvent.
COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8003

# Indispensable : docker-compose.yml utilise « condition: service_healthy ».
# Sans HEALTHCHECK, le conteneur ne devient jamais « healthy » et la gateway
# ne démarre pas. wget est fourni par busybox dans l'image Alpine.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:8003/health || exit 1

# --host 0.0.0.0 est OBLIGATOIRE : par défaut uvicorn n'écoute que sur
# 127.0.0.1, donc uniquement depuis l'intérieur du conteneur.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
