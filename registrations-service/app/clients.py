import logging

import httpx
from fastapi import HTTPException

from app import config

logger = logging.getLogger(__name__)

# Sans timeout, un service bloqué bloquerait aussi celui-ci, puis la
# gateway, puis le navigateur : une panne isolée devient une panne totale.
TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def _call(method: str, url: str, *, not_found: str, conflict: str | None = None):
    try:
        response = httpx.request(method, url, timeout=TIMEOUT)
    except httpx.RequestError as exc:
        logger.error("upstream unreachable %s: %s", url, exc)
        raise HTTPException(status_code=503, detail=f"service unavailable: {exc}")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=not_found)
    if conflict and response.status_code == 409:
        raise HTTPException(status_code=409, detail=conflict)
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502, detail=f"upstream error: {response.status_code}"
        )
    return response.json()


def get_participant(participant_id: int):
    """Vérifie auprès de participants-service que le participant existe."""
    return _call(
        "GET",
        f"{config.PARTICIPANTS_SERVICE_URL}/api/participants/{participant_id}",
        not_found="participant not found",
    )


def reserve_seat(event_id: int):
    """Réserve une place auprès d'events-service.

    C'est events-service qui détient le compteur et applique le verrou :
    deux inscriptions simultanées ne peuvent pas prendre la même dernière
    place. Un simple « lire la disponibilité puis insérer » ne le garantit
    pas et permettrait de dépasser la capacité.
    """
    return _call(
        "POST",
        f"{config.EVENTS_SERVICE_URL}/api/events/{event_id}/seats/reserve",
        not_found="event not found",
        conflict="event is full",
    )


def release_seat(event_id: int) -> None:
    """Libère une place : annulation, ou compensation après un échec local."""
    url = f"{config.EVENTS_SERVICE_URL}/api/events/{event_id}/seats/release"
    try:
        httpx.post(url, timeout=TIMEOUT)
    except httpx.RequestError as exc:
        # On journalise sans échouer : l'annulation locale doit aboutir même
        # si events-service est momentanément injoignable.
        logger.warning("could not release seat for event %s: %s", event_id, exc)
