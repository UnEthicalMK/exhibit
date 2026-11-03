import logging

from fastapi import FastAPI, HTTPException, Path

from .actions import allowed_actions
from .config import settings
from .paypal_client import PayPalClient, PayPalError

log = logging.getLogger("exhibit")
app = FastAPI(title="Exhibit")
paypal = PayPalClient()


def summarize(d: dict) -> dict:
    return {
        "id": d.get("dispute_id"),
        "reason": d.get("reason"),
        "status": d.get("status"),
        "stage": d.get("dispute_life_cycle_stage"),
        "amount": d.get("dispute_amount"),
        "seller_response_due_date": d.get("seller_response_due_date"),
        "buyer_response_due_date": d.get("buyer_response_due_date"),
    }


def paypal_get(path: str) -> dict:
    try:
        return paypal.request("GET", path)
    except PayPalError as err:
        log.warning("PayPal error: %s", err)
        raise HTTPException(status_code=502, detail=f"PayPal error {err.status_code}")


@app.get("/health")
def health():
    return {"ok": True, "paypal_env": settings.paypal_env}


@app.get("/disputes")
def list_disputes():
    data = paypal_get("/v1/customer/disputes")
    return [summarize(item) for item in data.get("items", [])]


@app.get("/disputes/{dispute_id}")
def get_dispute(dispute_id: str = Path(pattern=r"^[A-Za-z0-9-]+$", max_length=255)):
    data = paypal_get(f"/v1/customer/disputes/{dispute_id}")
    return {**summarize(data), "allowed_actions": allowed_actions(data)}