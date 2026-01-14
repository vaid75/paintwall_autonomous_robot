# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_generate_and_get_trajectory():
    payload = {
        "wall_width": 2.0,
        "wall_height": 1.0,
        "step": 0.2,
        "obstacles": []
    }
    r = client.post("/generate_trajectory", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "id" in body and "path_length" in body
    tid = body["id"]

    r2 = client.get(f"/trajectory/{tid}")
    assert r2.status_code == 200
    tdata = r2.json()
    assert float(tdata["wall_width"]) == 2.0
    path = json.loads(tdata["path"])
    assert isinstance(path, list)
