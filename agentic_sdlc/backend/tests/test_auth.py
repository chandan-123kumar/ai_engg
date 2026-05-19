import pytest
from src.auth.service import hash_password, verify_password, create_token, decode_token

# --- Auth Service Tests ---

def test_hash_password_returns_different_string():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert len(hashed) > 20

def test_verify_password_correct():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True

def test_verify_password_wrong():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False

def test_create_and_decode_token():
    token = create_token(user_id="abc-123", email="test@example.com")
    payload = decode_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["email"] == "test@example.com"

def test_decode_invalid_token_raises():
    with pytest.raises(Exception):
        decode_token("not.a.valid.token")


# --- Auth Router Tests (need DB) ---

@pytest.mark.asyncio
async def test_register_creates_user(client, setup_db):
    response = await client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "strongpass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "password_hash" not in data

@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client, setup_db):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "pass"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_returns_token(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "pass123"
    })
    response = await client.post("/auth/login", json={
        "email": "alice@example.com", "password": "pass123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password_fails(client, setup_db):
    await client.post("/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "pass123"
    })
    response = await client.post("/auth/login", json={
        "email": "alice@example.com", "password": "wrong"
    })
    assert response.status_code == 401
