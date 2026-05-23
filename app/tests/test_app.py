def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_returns_json_message(client):
    response = client.get("/")
    data = response.get_json()
    assert "message" in data


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ready_returns_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_metrics_returns_200(client):
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_contains_request_counter(client):
    client.get("/")
    response = client.get("/metrics")
    assert b"http_requests_total" in response.data


def test_metrics_contains_request_latency(client):
    client.get("/")
    response = client.get("/metrics")
    assert b"http_request_duration_seconds" in response.data


def test_metrics_content_type_is_text(client):
    response = client.get("/metrics")
    assert "text/plain" in response.content_type
