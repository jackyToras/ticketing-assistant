import uuid

from fastapi.testclient import TestClient

from src.api import app
from src.database import Base, SessionLocal, engine
from src.decision import GeneratedDecision
from src.models import Ticket, User


Base.metadata.create_all(engine)
client = TestClient(app)


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex}@example.com"


def register_and_login() -> tuple[dict, str]:
    email = unique_email()
    registration = client.post("/register", json={"email": email, "password": "safe-password-123"})
    assert registration.status_code == 201
    login = client.post("/login", json={"email": email, "password": "safe-password-123"})
    assert login.status_code == 200
    return registration.json(), login.json()["access_token"]


def test_registered_user_can_read_own_profile():
    user, token = register_and_login()
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


def test_user_cannot_read_another_users_ticket():
    _, alice_token = register_and_login()
    bob_response, _ = register_and_login()
    db = SessionLocal()
    try:
        ticket = Ticket(user_id=bob_response["id"], message="Bob's private ticket")
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        response = client.get(f"/tickets/{ticket.id}", headers={"Authorization": f"Bearer {alice_token}"})
    finally:
        db.close()
    assert response.status_code == 404


def test_ticket_decision_is_persisted(monkeypatch):
    def fake_decision(_):
        return GeneratedDecision(
            action="REQUEST_PHOTOS",
            confidence=0.91,
            reason="Policy requires photos for this order value.",
            sources=["damaged_goods.md"],
        )

    monkeypatch.setattr("src.api.create_decision", fake_decision)
    _, token = register_and_login()
    response = client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "My order arrived damaged.", "order_value_inr": 3500, "days_since_delivery": 1},
    )
    assert response.status_code == 201
    assert response.json()["decision"]["action"] == "REQUEST_PHOTOS"
    history = client.get("/tickets", headers={"Authorization": f"Bearer {token}"})
    assert history.status_code == 200
    assert len(history.json()) == 1
