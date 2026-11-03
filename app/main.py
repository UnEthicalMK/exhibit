import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path
from sqlmodel import Session, select

from .config import settings
from .db import get_session, init_db
from .models import Dispute
from .paypal_client import PayPalClient, PayPalError
from .sync import sync_all

log = logging.getLogger("exhibit")
paypal = PayPalClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Exhibit", lifespan=lifespan)


def summarize(d: Dispute) -> dict:
    return {
        "id": d.id,
        "reason": d.reason,
        "status": d.status,
        "stage": d.stage,
        "amount": {"value": d.amount_value, "currency_code": d.amount_currency},
        "seller_response_due_date": d.seller_response_due_date,
        "allowed_actions": d.allowed_actions,
        "synced_at": d.synced_at,
    }


@app.get("/health")
def health():
    return {"ok": True, "paypal_env": settings.paypal_env}


@app.post("/sync")
def sync(session: Session = Depends(get_session)):
    try:
        disputes = sync_all(session, paypal)
    except PayPalError as err:
        log.warning("PayPal error: %s", err)
        raise HTTPException(status_code=502, detail=f"PayPal error {err.status_code}")
    return {"synced": len(disputes)}


@app.get("/disputes")
def list_disputes(session: Session = Depends(get_session)):
    return [summarize(d) for d in session.exec(select(Dispute)).all()]


@app.get("/disputes/{dispute_id}")
def get_dispute(
    dispute_id: str = Path(pattern=r"^[A-Za-z0-9-]+$", max_length=255),
    session: Session = Depends(get_session),
):
    dispute = session.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Not synced yet. Run POST /sync first.")
    return summarize(dispute)