import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

os.environ.setdefault("LIVEKIT_API_KEY", "test-key")
os.environ.setdefault("LIVEKIT_API_SECRET", "test-secret")

from app.api import meetings
from app.main import app
from app.models.db import get_session


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch):
    monkeypatch.setenv("BACKEND_API_TOKEN", "test-api-token")


@pytest.fixture()
def client(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(meetings, "generate_room_token", lambda room, identity: ("test-token", str(room)))
    monkeypatch.setattr(meetings, "send_email", lambda *args: True)
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def headers():
    return {"X-API-Key": "test-api-token"}


def test_protected_endpoints_require_an_api_key(client):
    response = client.post("/api/meetings/", json={"title": "Planning", "host_email": "host@example.com"})

    assert response.status_code == 401


def test_create_start_and_ingest_a_meeting(client, headers):
    create_response = client.post(
        "/api/meetings/",
        headers=headers,
        json={"title": "Planning", "host_email": "host@example.com"},
    )

    assert create_response.status_code == 200
    meeting_id = create_response.json()["meeting_id"]

    start_response = client.post(f"/api/meetings/{meeting_id}/start", headers=headers)
    ingest_response = client.post(
        f"/api/meetings/{meeting_id}/ingest-transcript",
        headers=headers,
        json={"ts_start": 0, "ts_end": 10, "speaker": "Alex", "text": "We agreed to ship on Friday."},
    )
    summaries_response = client.get(f"/api/meetings/{meeting_id}/summaries", headers=headers)

    assert start_response.json() == {"status": "started"}
    assert ingest_response.status_code == 200
    assert summaries_response.json() == []


def test_invitation_uses_configured_frontend_url(client, headers, monkeypatch):
    sent_messages = []
    monkeypatch.setenv("FRONTEND_URL", "https://meeting-helper.example")
    monkeypatch.setattr(meetings, "send_email", lambda *args: sent_messages.append(args) or True)

    meeting_id = client.post(
        "/api/meetings/",
        headers=headers,
        json={"title": "Planning", "host_email": "host@example.com"},
    ).json()["meeting_id"]
    response = client.post(
        f"/api/meetings/{meeting_id}/invite",
        headers=headers,
        json={"emails": ["guest@example.com"]},
    )

    assert response.json() == {"invited": ["guest@example.com"]}
    assert "https://meeting-helper.example/rooms/" in sent_messages[0][2]
