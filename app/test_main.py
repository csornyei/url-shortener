from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.db import Base, engine
from app.cache import Cache

cache = Cache()

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def create_url():
    payload = {"url": "https://www.example.com"}
    response = client.post("/shorten", json=payload, follow_redirects=False)
    assert response.status_code == 201
    location_url = response.json()["location"]
    shortcode = location_url.split("/")[2]
    assert len(shortcode) == 6
    return shortcode

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}

def test_shorten_url_no_url():
    body = {}
    response = client.post("/shorten", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "URL is required"}


def test_shorten_url_create_url():
    payload = {"url": "https://www.example.com"}
    response = client.post("/shorten", json=payload, follow_redirects=False)
    assert response.status_code == 201
    location_url = response.json()["location"]
    shortcode = location_url.split("/")[2]
    assert len(shortcode) == 6

def test_shorten_url_existing_url():
    shortcode = create_url()

    response = client.post("/shorten", json={"url": "https://www.example.com"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/urls/{shortcode}"

def test_redirect_url_no_url():
    response = client.get("/urls/abc123", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "There is no url with this shortcode"}

def test_redirect_url_cache():
    shortcode = create_url()

    assert cache.retrieve_url(shortcode) == "https://www.example.com"

    response = client.get(f"/urls/{shortcode}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.example.com"

def test_redirect_url_db():
    shortcode = create_url()

    cache.client.delete(shortcode)

    assert cache.retrieve_url(shortcode) == None

    response = client.get(f"/urls/{shortcode}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.example.com"

def test_redirect_url_recache_url():
    shortcode = create_url()

    cache.client.delete(shortcode)

    assert cache.retrieve_url(shortcode) == None

    response = client.get(f"/urls/{shortcode}", follow_redirects=False)

    assert cache.retrieve_url(shortcode) == "https://www.example.com"

def test_redirect_url_extend_url_ttl():
    shortcode = create_url()

    client.get(f"/urls/{shortcode}", follow_redirects=False)

    assert cache.retrieve_url(shortcode) == "https://www.example.com"

    assert cache.client.ttl(shortcode) >= 24 * 60 * 60

def test_url_stats_no_url():
    response = client.get("/urls/abc123/stats", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "There is no url with this shortcode"}

def test_url_stats_no_hits():
    shortcode = create_url()

    response = client.get(f"/urls/{shortcode}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["hits"] == 0
    assert data["url"] == "https://www.example.com"

def test_url_stats_with_hits():
    shortcode = create_url()

    for _ in range(10):
        response = client.get(f"/urls/{shortcode}")

    response = client.get(f"/urls/{shortcode}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["hits"] == 10
    assert data["url"] == "https://www.example.com"

# Unfortunately, I'm not using Python on a daily basis and the mocking proven to be more complicated than I thought.
# Here is an attempt to mock the database to return an integrity error when adding a new URL.
""" def test_shorten_url_existing_url():
    db_mock = MagicMock()

    db_mock.add.side_effect = IntegrityError("statement", "params", "orig", "detail")

    db_mock.query.return_value.filter.return_value.first.return_value = {
        "id": 1,
        "url": "https://www.example.com",
        "shortcode": "abc123",
    }

    app.dependency_overrides["get_db"] = lambda: db_mock

    payload = {"url": "https://www.example.com"}

    response = client.post("/shorten", json=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/urls/abc123"
"""