import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

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

BASE = "/api/participants"


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def payload(**overrides):
    base = {
        "full_name": "Aichatou Ndaw",
        "email": "aichatou@dit.sn",
        "phone": "+221770000000",
        "type": "etudiant",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------- santé -----
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "participants-service"


def test_routes_are_served_under_api_prefix():
    """La gateway route /api/participants : le service doit y répondre."""
    assert client.get(BASE).status_code == 200
    assert client.get("/participants").status_code == 404


# ---------------------------------------------------------------- CRUD -----
def test_create_participant():
    response = client.post(BASE, json=payload())
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "aichatou@dit.sn"
    assert body["type"] == "etudiant"


def test_duplicate_email_is_rejected():
    client.post(BASE, json=payload())
    assert client.post(BASE, json=payload()).status_code == 409


def test_invalid_email_is_rejected():
    assert client.post(BASE, json=payload(email="pas-un-email")).status_code == 422


def test_invalid_type_is_rejected():
    assert client.post(BASE, json=payload(type="alien")).status_code == 422


def test_short_name_is_rejected():
    assert client.post(BASE, json=payload(full_name="a")).status_code == 422


def test_get_unknown_participant_returns_404():
    assert client.get(f"{BASE}/9999").status_code == 404


def test_update_participant():
    pid = client.post(BASE, json=payload()).json()["id"]
    response = client.put(f"{BASE}/{pid}", json={"type": "professeur"})
    assert response.status_code == 200
    assert response.json()["type"] == "professeur"


def test_update_to_existing_email_is_rejected():
    client.post(BASE, json=payload())
    pid = client.post(
        BASE, json=payload(full_name="Kra Junior", email="kra@dit.sn")
    ).json()["id"]

    response = client.put(f"{BASE}/{pid}", json={"email": "aichatou@dit.sn"})
    assert response.status_code == 409


def test_delete_participant():
    pid = client.post(BASE, json=payload()).json()["id"]
    assert client.delete(f"{BASE}/{pid}").status_code == 204
    assert client.get(f"{BASE}/{pid}").status_code == 404


# ------------------------------------------------------------ recherche -----
def test_search_by_name():
    client.post(BASE, json=payload())
    client.post(BASE, json=payload(full_name="Kra Junior", email="kra@dit.sn"))

    found = client.get(BASE, params={"search": "Kra"}).json()
    assert len(found) == 1
    assert found[0]["full_name"] == "Kra Junior"


def test_search_by_email():
    client.post(BASE, json=payload())
    client.post(BASE, json=payload(full_name="Kra Junior", email="kra@dit.sn"))

    found = client.get(BASE, params={"search": "aichatou"}).json()
    assert len(found) == 1


def test_search_without_match_returns_empty():
    client.post(BASE, json=payload())
    assert client.get(BASE, params={"search": "zzzz"}).json() == []
