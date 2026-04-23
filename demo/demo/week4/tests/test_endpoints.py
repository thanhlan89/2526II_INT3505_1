import pytest

from app import OPENAPI_PATH, app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_root_redirects_to_docs(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/docs")


def test_openapi_yaml_returns_yaml_content(client):
    response = client.get("/openapi.yaml")
    assert response.status_code == 200
    assert response.mimetype in {"text/yaml", "application/x-yaml", "text/plain"}
    assert "openapi: 3.0.3" in response.get_data(as_text=True)


def test_openapi_yaml_returns_404_when_file_missing(client, monkeypatch):
    missing_file = OPENAPI_PATH.with_name("openapi_missing.yaml")
    monkeypatch.setattr("app.OPENAPI_PATH", missing_file)

    response = client.get("/openapi.yaml")
    assert response.status_code == 404
    assert response.get_json() == {"error": "openapi.yaml not found"}


def test_docs_returns_swagger_ui_html(client):
    response = client.get("/docs")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert "SwaggerUIBundle" in html
    assert 'url: "/openapi.yaml"' in html
