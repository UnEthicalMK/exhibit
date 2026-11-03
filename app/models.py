from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Dispute(SQLModel, table=True):
    id: str = Field(primary_key=True)  # PayPal's dispute_id, e.g. PP-R-...
    reason: str | None = None
    status: str | None = None
    stage: str | None = None
    amount_value: str | None = None  # PayPal sends amounts as strings; keep them exact
    amount_currency: str | None = None
    seller_response_due_date: str | None = None
    paypal_update_time: str | None = None
    allowed_actions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON))  # full PayPal response
    synced_at: datetime = Field(default_factory=utcnow)