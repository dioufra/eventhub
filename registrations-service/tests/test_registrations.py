import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import clients
from app.database import Base, get_db
from app.main import app

# SQLite en mémoire : aucun fichier laissé sur le disque, aucun conteneur
# requis. StaticPool garde une connexion unique, sinon chaque session
# repartirait d'une base vide.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

BASE = "/api/registrations"

EVENT_UNKNOWN = 404
EVENT_FULL = 409
PARTICIPANT_UNKNOWN = 404


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def stub_remote_services(monkeypatch):
    """Neutralise les appels HTTP : un test unitaire ne dépend d'aucun service.

    Le compteur renvoyé permet de vérifier que la réservation et la
    libération de place sont bien déclenchées.
    """
    calls = {"participant": 0, "reserve": 0, "release": 0}

    def fake_get_participant(participant_id: int):
        calls["participant"] += 1
        if participant_id == PARTICIPANT_UNKNOWN:
            raise HTTPException(status_code=404, detail="participant not found")
        return {"id": participant_id, "full_name": "Test Participant"}

    def fake_reserve_seat(event_id: int):
        calls["reserve"] += 1
        if event_id == EVENT_UNKNOWN:
            raise HTTPException(status_code=404, detail="event not found")
        if event_id == EVENT_FULL:
            raise HTTPException(status_code=409, detail="event is full")
        return {"event_id": event_id, "seats_available": 9, "is_full": False}

    def fake_release_seat(event_id: int):
        calls["release"] += 1

    monkeypatch.setattr(clients, "get_participant", fake_get_participant)
    monkeypatch.setattr(clients, "reserve_seat", fake_reserve_seat)
    monkeypatch.setattr(clients, "release_seat", fake_release_seat)
    return calls


# --------------------------------------------------------------- santé -----
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "registrations-service"


def test_routes_are_served_under_api_prefix():
    """La gateway route /api/registrations : le service doit y répondre."""
    assert client.get(f"{BASE}/stats").status_code == 200
    assert client.get("/registrations/stats").status_code == 404


# --------------------------------------------------------- inscription -----
def test_create_registration_calls_both_services(stub_remote_services):
    response = client.post(BASE, json={"event_id": 1, "participant_id": 1})

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"] == 1
    assert body["status"] == "confirmed"
    # C'est la démonstration de l'architecture microservices.
    assert stub_remote_services["participant"] == 1
    assert stub_remote_services["reserve"] == 1


def test_duplicate_registration_is_rejected(stub_remote_services):
    client.post(BASE, json={"event_id": 1, "participant_id": 1})
    response = client.post(BASE, json={"event_id": 1, "participant_id": 1})

    assert response.status_code == 409
    # Le doublon est détecté localement : aucune place n'est réservée en trop.
    assert stub_remote_services["reserve"] == 1


def test_unknown_participant_is_rejected(stub_remote_services):
    response = client.post(
        BASE, json={"event_id": 1, "participant_id": PARTICIPANT_UNKNOWN}
    )
    assert response.status_code == 404
    # Le participant est vérifié AVANT de réserver une place.
    assert stub_remote_services["reserve"] == 0


def test_unknown_event_is_rejected():
    response = client.post(BASE, json={"event_id": EVENT_UNKNOWN, "participant_id": 1})
    assert response.status_code == 404


def test_full_event_is_rejected():
    response = client.post(BASE, json={"event_id": EVENT_FULL, "participant_id": 1})
    assert response.status_code == 409


# ---------------------------------------------------------- annulation -----
def test_cancel_releases_the_seat(stub_remote_services):
    created = client.post(BASE, json={"event_id": 2, "participant_id": 2}).json()

    assert client.delete(f"{BASE}/{created['id']}").status_code == 204
    assert stub_remote_services["release"] == 1
    assert client.get(f"{BASE}/event/2").json() == []


def test_cancel_twice_releases_only_one_seat(stub_remote_services):
    created = client.post(BASE, json={"event_id": 2, "participant_id": 2}).json()

    client.delete(f"{BASE}/{created['id']}")
    client.delete(f"{BASE}/{created['id']}")
    assert stub_remote_services["release"] == 1


def test_cancel_unknown_registration():
    assert client.delete(f"{BASE}/999").status_code == 404


def test_reregistration_after_cancel(stub_remote_services):
    created = client.post(BASE, json={"event_id": 8, "participant_id": 8}).json()
    client.delete(f"{BASE}/{created['id']}")

    response = client.post(BASE, json={"event_id": 8, "participant_id": 8})
    assert response.status_code == 201
    assert stub_remote_services["reserve"] == 2


# ------------------------------------------------------------- listes -----
def test_list_by_event():
    client.post(BASE, json={"event_id": 3, "participant_id": 10})
    client.post(BASE, json={"event_id": 3, "participant_id": 11})
    client.post(BASE, json={"event_id": 99, "participant_id": 12})

    assert len(client.get(f"{BASE}/event/3").json()) == 2


def test_list_by_participant():
    client.post(BASE, json={"event_id": 4, "participant_id": 20})
    client.post(BASE, json={"event_id": 5, "participant_id": 20})

    assert len(client.get(f"{BASE}/participant/20").json()) == 2


def test_stats():
    client.post(BASE, json={"event_id": 6, "participant_id": 30})
    client.post(BASE, json={"event_id": 6, "participant_id": 31})
    client.post(BASE, json={"event_id": 7, "participant_id": 32})

    body = client.get(f"{BASE}/stats").json()
    assert body["total"] == 3
    assert len(body["by_event"]) == 2


def test_stats_ignores_cancelled():
    created = client.post(BASE, json={"event_id": 6, "participant_id": 30}).json()
    client.delete(f"{BASE}/{created['id']}")

    assert client.get(f"{BASE}/stats").json()["total"] == 0
