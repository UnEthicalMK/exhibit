import json, sys, uuid
from pathlib import Path
import requests

BASE = "https://api-m.sandbox.paypal.com"

EVIDENCE = {
    "PROOF_OF_FULFILLMENT": {
        "evidence_type": "PROOF_OF_FULFILLMENT",
        "evidence_info": {"tracking_info": [
            {"carrier_name": "FEDEX", "tracking_number": "122533485"}]},
        "notes": "Sandbox test: shipped with tracking.",
    },
    "OTHER": {
        "evidence_type": "OTHER",
        "notes": "Sandbox test: the item was delivered to the buyer's address.",
    },
}

env = {}
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
if env.get("PAYPAL_ENV") != "SANDBOX":
    raise SystemExit("Stopping: PAYPAL_ENV must be SANDBOX")

dispute_id = sys.argv[1]
evidence_type = sys.argv[2] if len(sys.argv) > 2 else "PROOF_OF_FULFILLMENT"
if evidence_type not in EVIDENCE:
    raise SystemExit("Evidence type must be one of: " + ", ".join(EVIDENCE))

token = requests.post(
    BASE + "/v1/oauth2/token",
    auth=(env["PAYPAL_CLIENT_ID"], env["PAYPAL_CLIENT_SECRET"]),
    data={"grant_type": "client_credentials"},
).json()["access_token"]
headers = {"Authorization": "Bearer " + token}

case = requests.get(f"{BASE}/v1/customer/disputes/{dispute_id}", headers=headers).json()
if "provide_evidence" not in [link["rel"] for link in case.get("links", [])]:
    raise SystemExit(f"No provide_evidence link. Status is {case.get('status')}. Nothing sent.")

payload = {"evidences": [EVIDENCE[evidence_type]]}
print("About to send this to", dispute_id)
print(json.dumps(payload, indent=2))
if input("Type YES to send (sandbox only): ") != "YES":
    raise SystemExit("Cancelled. Nothing sent.")

response = requests.post(
    f"{BASE}/v1/customer/disputes/{dispute_id}/provide-evidence",
    headers={**headers, "PayPal-Request-Id": str(uuid.uuid4())},
    files={"input": (None, json.dumps(payload), "application/json")},
)
print(response.status_code)
print(response.text)