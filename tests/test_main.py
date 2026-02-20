from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"].startswith("Welcome")


def test_create_and_get_item():
    resp = client.post("/api/items", json={"name": "Test item", "description": "desc"})
    assert resp.status_code == 201
    item = resp.json()
    assert item["id"] == 1
    res2 = client.get(f"/api/items/{item['id']}")
    assert res2.status_code == 200
    assert res2.json()["name"] == "Test item"
