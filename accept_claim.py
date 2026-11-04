import json, sys, uuid
from pathlib import Path
import requests

BASE = "https://api-m.sandbox.paypal.com"

env = {}
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
if env.get("PAYPAL_ENV") != "SANDBOX":
    raise SystemExit("Stopping: PAYPAL_ENV must be SANDBOX")

dispute_id = sys.argv[1]
token = requests.post(
    BASE + "/v1/oauth2/token",
    auth=(env["PAYPAL_CLIENT_ID"], env["PAYPAL_CLIENT_SECRET"]),
    data={"grant_type": "client_credentials"},
).json()["access_token"]
headers = {"Authorization": "Bearer " + token}

case = requests.get(f"{BASE}/v1/customer/disputes/{dispute_id}", headers=headers).json()
links = [link["rel"] for link in case.get("links", [])]
allowed = (case.get("allowed_response_options", {})
               .get("accept_claim", {}).get("accept_claim_types", []))
if "accept_claim" not in links or "REFUND" not in allowed:
    raise SystemExit(f"PayPal doesn't allow a full refund here. Status is {case.get('status')}. Nothing sent.")

payload = {"note": "Sandbox test: accepting the claim and refunding the buyer.",
           "accept_claim_type": "REFUND"}
amount = case.get("dispute_amount", {})
print("About to ACCEPT the claim on", dispute_id, "and refund",
      amount.get("value"), amount.get("currency_code"))
print(json.dumps(payload, indent=2))
if input("Type YES to send (sandbox only): ") != "YES":
    raise SystemExit("Cancelled. Nothing sent.")

response = requests.post(
    f"{BASE}/v1/customer/disputes/{dispute_id}/accept-claim",
    headers={**headers, "PayPal-Request-Id": str(uuid.uuid4())},
    files={"input": (None, json.dumps(payload), "application/json")},
)
print(response.status_code)
print(response.text)