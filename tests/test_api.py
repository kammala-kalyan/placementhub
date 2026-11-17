"""API route tests using the fake store and fakeredis."""

SAMPLE = """Company: Nimbus Analytics
Role: Data Analyst
CTC: 7.5 LPA
Apply: https://careers.nimbus-analytics.example/apply/da-2027"""


def test_ingest_creates_then_detects_duplicate(client, store):
    first = client.post("/ingest", json={"text": SAMPLE, "source": "test"})
    assert first.status_code == 201
    assert first.json()["status"] == "created"
    assert first.json()["job"]["category"] == "Full-time"

    # Same message with different emojis/case/spacing -> same hash -> duplicate.
    again = client.post("/ingest", json={"text": "🔥 " + SAMPLE.upper() + "  ", "source": "test"})
    assert again.status_code == 200
    assert again.json()["status"] == "duplicate"
    assert again.json()["id"] == first.json()["id"]
    assert len(store.jobs) == 1


def test_ingest_rejects_too_short_text(client):
    assert client.post("/ingest", json={"text": "hi"}).status_code == 422


def test_get_job_and_404(client):
    job_id = client.post("/ingest", json={"text": SAMPLE}).json()["id"]
    assert client.get(f"/jobs/{job_id}").json()["apply_link"].endswith("da-2027")
    assert client.get("/jobs/does-not-exist").status_code == 404


def test_search_second_call_is_served_from_cache(client, store):
    client.post("/ingest", json={"text": SAMPLE})
    first = client.get("/jobs/search", params={"q": "analyst"})
    second = client.get("/jobs/search", params={"q": "analyst"})
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert store.search_calls == 1          # ES was only queried once
    assert second.json()["total"] == 1


def test_search_still_works_when_redis_is_down(client, store, redis_server):
    client.post("/ingest", json={"text": SAMPLE})
    redis_server.connected = False          # simulate Redis outage
    resp = client.get("/jobs/search", params={"q": "analyst"})
    assert resp.status_code == 200
    assert resp.json()["cached"] is False
    assert resp.json()["total"] == 1


def test_search_validates_category(client):
    assert client.get("/jobs/search", params={"category": "Party"}).status_code == 422


def test_health_ok_degraded_down(client, store, redis_server):
    assert client.get("/health").json() == {"status": "ok", "elasticsearch": "up", "redis": "up"}

    redis_server.connected = False
    assert client.get("/health").json()["status"] == "degraded"

    store.up = False
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "down"


def test_metrics_endpoint_exposes_prometheus_text(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert "placementhub_http_requests_total" in body
