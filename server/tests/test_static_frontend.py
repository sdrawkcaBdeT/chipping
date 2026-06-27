from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_static_frontend_serves_spa_routes(monkeypatch, tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>Observer Mode</body></html>")

    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    get_settings.cache_clear()

    client = TestClient(create_app())

    root_response = client.get("/")
    me_response = client.get("/me/login")

    assert root_response.status_code == 200
    assert "Observer Mode" in root_response.text
    assert me_response.status_code == 200
    assert "Observer Mode" in me_response.text

    get_settings.cache_clear()
