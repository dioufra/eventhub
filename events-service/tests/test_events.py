import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# SQLite en mémoire : les tests ne dépendent d'aucun conteneur ni réseau.
# StaticPool garde une seule connexion, sinon chaque session repartirait
# d'une base vide.
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

BASE = "/api/events"


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def payload(**overrides):
    base = {
        "title": "Conference DevOps",
        "description": "Introduction au CI/CD",
        "starts_at": "2026-09-15T10:00:00",
        "location": "Amphi A",
        "capacity": 50,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------- santé -----
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_routes_are_served_under_api_prefix():
    """La gateway route /api/events : le service doit répondre sur ce préfixe."""
    assert client.get(BASE).status_code == 200
    assert client.get("/events").status_code == 404


# ---------------------------------------------------------------- CRUD -----
def test_create_event():
    response = client.post(BASE, json=payload())
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Conference DevOps"
    assert body["seats_taken"] == 0


def test_create_rejects_negative_capacity():
    assert client.post(BASE, json=payload(capacity=-5)).status_code == 422


def test_create_rejects_short_title():
    assert client.post(BASE, json=payload(title="a")).status_code == 422


def test_get_unknown_event_returns_404():
    assert client.get(f"{BASE}/9999").status_code == 404


def test_update_event():
    event_id = client.post(BASE, json=payload()).json()["id"]
    response = client.put(f"{BASE}/{event_id}", json={"location": "Salle C"})
    assert response.status_code == 200
    assert response.json()["location"] == "Salle C"


def test_delete_event():
    event_id = client.post(BASE, json=payload()).json()["id"]
    assert client.delete(f"{BASE}/{event_id}").status_code == 204
    assert client.get(f"{BASE}/{event_id}").status_code == 404


# ------------------------------------------------------------- filtres -----
def test_filter_by_location():
    client.post(BASE, json=payload(location="Amphi A"))
    client.post(BASE, json=payload(location="Salle B"))

    assert len(client.get(BASE).json()) == 2
    filtered = client.get(BASE, params={"location": "Amphi"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


def test_filter_by_date():
    client.post(BASE, json=payload(starts_at="2026-09-15T10:00:00"))
    client.post(BASE, json=payload(starts_at="2026-10-20T10:00:00"))

    assert len(client.get(BASE, params={"date": "2026-09-15"}).json()) == 1


# -------------------------------------------------------- disponibilité -----
def test_availability_of_new_event():
    event_id = client.post(BASE, json=payload(capacity=10)).json()["id"]
    body = client.get(f"{BASE}/{event_id}/availability").json()

    assert body["seats_available"] == 10
    assert body["is_full"] is False


def test_reserve_decreases_availability():
    event_id = client.post(BASE, json=payload(capacity=2)).json()["id"]

    assert client.post(f"{BASE}/{event_id}/seats/reserve").status_code == 200
    body = client.get(f"{BASE}/{event_id}/availability").json()
    assert body["seats_taken"] == 1
    assert body["seats_available"] == 1


def test_reserve_fails_when_full():
    """Le contrôle qui empêche d'inscrire 51 personnes pour 50 places."""
    event_id = client.post(BASE, json=payload(capacity=1)).json()["id"]

    assert client.post(f"{BASE}/{event_id}/seats/reserve").status_code == 200
    assert client.post(f"{BASE}/{event_id}/seats/reserve").status_code == 409

    body = client.get(f"{BASE}/{event_id}/availability").json()
    assert body["is_full"] is True


def test_release_frees_a_seat():
    event_id = client.post(BASE, json=payload(capacity=1)).json()["id"]
    client.post(f"{BASE}/{event_id}/seats/reserve")
    client.post(f"{BASE}/{event_id}/seats/release")

    assert client.get(f"{BASE}/{event_id}/availability").json()["seats_available"] == 1


def test_release_never_goes_below_zero():
    event_id = client.post(BASE, json=payload(capacity=5)).json()["id"]
    client.post(f"{BASE}/{event_id}/seats/release")

    assert client.get(f"{BASE}/{event_id}/availability").json()["seats_taken"] == 0


def test_reserve_on_unknown_event_returns_404():
    assert client.post(f"{BASE}/9999/seats/reserve").status_code == 404


def test_capacity_cannot_drop_below_registrations():
    event_id = client.post(BASE, json=payload(capacity=5)).json()["id"]
    client.post(f"{BASE}/{event_id}/seats/reserve")
    client.post(f"{BASE}/{event_id}/seats/reserve")

    assert client.put(f"{BASE}/{event_id}", json={"capacity": 1}).status_code == 409
