from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unsigned_webhook_is_rejected():
    fake = {"id": "WH-FAKE-1", "event_type": "CUSTOMER.DISPUTE.CREATED",
            "resource": {"dispute_id": "PP-R-FAKE-1"}}
    response = client.post("/webhooks/paypal", json=fake)
    assert response.status_code == 400