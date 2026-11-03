import json
from pathlib import Path

from app.actions import allowed_actions

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_actions_from_real_waiting_case():
    case = json.loads((FIXTURES / "waiting_for_seller_response.json").read_text(encoding="utf-8"))
    assert allowed_actions(case) == sorted([
    "send_message", "accept_claim", "make_offer", "escalate", "provide_evidence",
])


def test_no_links_means_no_actions():
    assert allowed_actions({"links": [{"rel": "self"}]}) == []
    assert allowed_actions({}) == []