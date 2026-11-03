import json
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Dispute
from app.sync import upsert_dispute

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_resync_updates_one_row():
    engine = create_engine("sqlite://", poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    case = json.loads((FIXTURES / "waiting_for_seller_response.json").read_text(encoding="utf-8"))

    for _ in range(2):  # syncing the same case twice must not duplicate it
        with Session(engine) as session:
            upsert_dispute(session, case)
            session.commit()

    with Session(engine) as session:
        rows = session.exec(select(Dispute)).all()
    assert len(rows) == 1
    assert rows[0].status == "WAITING_FOR_SELLER_RESPONSE"
    assert rows[0].amount_value == "68.00"
    assert "provide_evidence" in rows[0].allowed_actions