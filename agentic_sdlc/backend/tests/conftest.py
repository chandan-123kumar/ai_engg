import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.database import Base, engine

@pytest.fixture
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
