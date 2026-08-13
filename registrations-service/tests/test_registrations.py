import os

os.environ["DATABASE_URL"] = "sqlite:///./test_registrations.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app import clients
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_registrations.db"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


def mock_get_event(event_id):
    if event_id == 404:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="event not found")
    return {"id": event_id, "title": "Test Event"}


def mock_get_participant(participant_id):
    if participant_id == 404:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="participant not found")
    return {"id": participant_id, "name": "Test Participant"}


def mock_get_availability(event_id):
    return {"event_id": event_id, "remaining": 10}


@pytest.fixture(autouse=True)
def mock_clients(monkeypatch):
    monkeypatch.setattr(clients, "get_event", mock_get_event)
    monkeypatch.setattr(clients, "get_participant", mock_get_participant)
    monkeypatch.setattr(clients, "get_event_availability", mock_get_availability)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "registrations-service"


def test_create_registration(client):
    response = client.post("/registrations/", json={"event_id": 1, "participant_id": 1})
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == 1
    assert data["participant_id"] == 1
    assert data["status"] == "confirmed"


def test_create_duplicate_registration(client):
    client.post("/registrations/", json={"event_id": 1, "participant_id": 1})
    response = client.post("/registrations/", json={"event_id": 1, "participant_id": 1})
    assert response.status_code == 409


def test_cancel_registration(client):
    response = client.post("/registrations/", json={"event_id": 2, "participant_id": 2})
    reg_id = response.json()["id"]
    cancel_response = client.post(f"/registrations/{reg_id}/cancel")
    assert cancel_response.status_code == 200
    data = cancel_response.json()
    assert data["status"] == "cancelled"


def test_cancel_unknown_registration(client):
    response = client.post("/registrations/999/cancel")
    assert response.status_code == 404


def test_list_by_event(client):
    client.post("/registrations/", json={"event_id": 3, "participant_id": 10})
    client.post("/registrations/", json={"event_id": 3, "participant_id": 11})
    response = client.get("/registrations/event/3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_by_participant(client):
    client.post("/registrations/", json={"event_id": 4, "participant_id": 20})
    client.post("/registrations/", json={"event_id": 5, "participant_id": 20})
    response = client.get("/registrations/participant/20")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_stats(client):
    client.post("/registrations/", json={"event_id": 6, "participant_id": 30})
    client.post("/registrations/", json={"event_id": 6, "participant_id": 31})
    client.post("/registrations/", json={"event_id": 7, "participant_id": 32})
    response = client.get("/registrations/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["by_event"]) == 2
