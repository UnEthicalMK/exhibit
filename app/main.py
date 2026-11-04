import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Request
from sqlmodel import Session, select

from .config import settings
from .db import engine, get_session, init_db
from .models import Dispute, WebhookEvent
from .paypal_client import PayPalClient, PayPalError
from .sync import sync_all, upsert_dispute
from .webhooks import verify_signature

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
log = logging.getLogger("exhibit")
paypal = PayPalClient()  # used by requests
poller_paypal = PayPalClient()  # used only by the background sync


def sync_once() -> int:
    with Session(engine) as session:
        return len(sync_all(session, poller_paypal))


async def poll_paypal() -> None:
    """Backup for webhooks: refresh every case from PayPal every few minutes."""
    while True:
        try:
            count = await asyncio.to_thread(sync_once)
            log.info("Background sync: %d dispute(s) up to date", count)
        except Exception as err:  # keep polling even if one round fails
            log.warning("Background sync failed: %s", err)
        await asyncio.sleep(settings.sync_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(poll_paypal())
    yield
    task.cancel()


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


@app.post("/webhooks/paypal")
def paypal_webhook(
    request: Request,
    event: dict = Body(...),
    session: Session = Depends(get_session),
):
    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="Not a PayPal event")
    try:
        verified = verify_signature(paypal, request.headers, event, settings.paypal_webhook_id)
    except PayPalError as err:
        log.warning("Could not verify webhook %s: %s", event_id, err)
        raise HTTPException(status_code=502, detail="Could not verify")  # PayPal retries later
    if not verified:
        log.warning("Rejected webhook %s: signature not verified", event_id)
        raise HTTPException(status_code=400, detail="Signature not verified")

    if session.get(WebhookEvent, event_id):
        return {"ok": True, "duplicate": True}  # PayPal may deliver the same event twice

    resource = event.get("resource") or {}
    record = WebhookEvent(
        id=event_id,
        event_type=event.get("event_type", ""),
        dispute_id=resource.get("dispute_id"),
        verified=True,
        raw=event,
    )
    session.add(record)
    if record.event_type.startswith("CUSTOMER.DISPUTE.") and record.dispute_id:
        detail = paypal.request("GET", f"/v1/customer/disputes/{record.dispute_id}")
        upsert_dispute(session, detail)
        record.processed = True
    session.commit()
    return {"ok": True}