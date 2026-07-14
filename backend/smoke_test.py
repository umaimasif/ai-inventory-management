"""Quick in-process smoke test of the auth flow (no server needed)."""
import os
import tempfile

# Use an isolated temp SQLite DB so the smoke test never touches real data.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def run() -> None:
    # `with` triggers startup events (table creation) before requests run.
    with TestClient(app) as client:
        _checks(client)


def _checks(client: TestClient) -> None:
    # Health
    r = client.get("/api/health")
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok"}

    # Register
    r = client.post(
        "/api/auth/register",
        json={
            "email": "manager@shop.com",
            "full_name": "Shop Manager",
            "password": "supersecret1",
        },
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert token
    assert r.json()["user"]["email"] == "manager@shop.com"

    # Duplicate register rejected
    r = client.post(
        "/api/auth/register",
        json={
            "email": "manager@shop.com",
            "full_name": "Dup",
            "password": "supersecret1",
        },
    )
    assert r.status_code == 400, r.text

    # Login
    r = client.post(
        "/api/auth/login",
        json={"email": "manager@shop.com", "password": "supersecret1"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # Wrong password
    r = client.post(
        "/api/auth/login",
        json={"email": "manager@shop.com", "password": "wrong"},
    )
    assert r.status_code == 401, r.text

    # /me with token
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "manager@shop.com"

    # /me without token
    r = client.get("/api/auth/me")
    assert r.status_code == 401, r.text

    print("SMOKE OK: health, register, dup-guard, login, bad-login, /me all pass")


if __name__ == "__main__":
    run()
