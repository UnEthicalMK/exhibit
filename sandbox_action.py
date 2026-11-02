import sys
from pathlib import Path
import requests

BASE = "https://api-m.sandbox.paypal.com"

ACTIONS = {  # name: (path suffix, request body)
    "escalate": ("escalate", {"note": "Sandbox test: escalating to a claim."}),
    "adjudicate_seller": ("adjudicate", {"adjudication_outcome": "SELLER_FAVOR"}),
    "adjudicate_buyer": ("adjudicate", {"adjudication_outcome": "BUYER_FAVOR"}),
    "require_seller_evidence": ("require-evidence", {"action": "SELLER_EVIDENCE"}),
    "require_buyer_evidence": ("require-evidence", {"action": "BUYER_EVIDENCE"}),
}

env = {}
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
if env.get("PAYPAL_ENV") != "SANDBOX":
    raise SystemExit("Stopping: PAYPAL_ENV must be SANDBOX")

dispute_id, name = sys.argv[1], sys.argv[2]
if name not in ACTIONS:
    raise SystemExit("Action must be one of: " + ", ".join(ACTIONS))
suffix, body = ACTIONS[name]

token = requests.post(
    BASE + "/v1/oauth2/token",
    auth=(env["PAYPAL_CLIENT_ID"], env["PAYPAL_CLIENT_SECRET"]),
    data={"grant_type": "client_credentials"},
).json()["access_token"]
headers = {"Authorization": "Bearer " + token}

case = requests.get(f"{BASE}/v1/customer/disputes/{dispute_id}", headers=headers).json()
allowed = [l["href"] for l in case.get("links", []) if l["href"].endswith("/" + suffix)]
print("status:", case.get("status"), "| stage:", case.get("dispute_life_cycle_stage"))
if not allowed:
    raise SystemExit(f"PayPal offers no '{suffix}' link on this case. Nothing sent.")

print("About to POST", allowed[0])
print(body)
if input("Type YES to send (sandbox only): ") != "YES":
    raise SystemExit("Cancelled. Nothing sent.")
response = requests.post(allowed[0], headers=headers, json=body)
print(response.status_code)
print(response.text)