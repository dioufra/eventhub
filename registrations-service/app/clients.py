import httpx
from fastapi import HTTPException
from app import config


def _call(method: str, url: str):
    try:
        response = httpx.request(method, url, timeout=5.0)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"service unavailable: {exc}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="resource not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"upstream error: {response.status_code}")
    return response.json()


def get_event(event_id: int):
    return _call("GET", f"{config.EVENTS_SERVICE_URL}/events/{event_id}")


def get_event_availability(event_id: int):
    return _call("GET", f"{config.EVENTS_SERVICE_URL}/events/{event_id}/availability")


def get_participant(participant_id: int):
    return _call("GET", f"{config.PARTICIPANTS_SERVICE_URL}/participants/{participant_id}")
