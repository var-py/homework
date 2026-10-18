def test_healthz(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "привет-привет" in response.get_data(as_text=True)
