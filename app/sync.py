from sqlmodel import Session

from .actions import allowed_actions
from .models import Dispute, utcnow


def upsert_dispute(session: Session, data: dict) -> Dispute:
    """Save one show-dispute response. Creates the row or updates it. The caller commits."""
    dispute = session.get(Dispute, data["dispute_id"]) or Dispute(id=data["dispute_id"])
    amount = data.get("dispute_amount") or {}
    dispute.reason = data.get("reason")
    dispute.status = data.get("status")
    dispute.stage = data.get("dispute_life_cycle_stage")
    dispute.amount_value = amount.get("value")
    dispute.amount_currency = amount.get("currency_code")
    dispute.seller_response_due_date = data.get("seller_response_due_date")
    dispute.paypal_update_time = data.get("update_time")
    dispute.allowed_actions = allowed_actions(data)
    dispute.raw = data
    dispute.synced_at = utcnow()
    session.add(dispute)
    return dispute


def sync_all(session: Session, paypal) -> list[Dispute]:
    """List disputes, then fetch each one in full: list items carry no action links."""
    listing = paypal.request("GET", "/v1/customer/disputes")
    synced = []
    for item in listing.get("items", []):  # one page is plenty for the sandbox
        detail = paypal.request("GET", f"/v1/customer/disputes/{item['dispute_id']}")
        synced.append(upsert_dispute(session, detail))
    session.commit()
    return synced