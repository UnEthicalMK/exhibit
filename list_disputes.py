import base64, json, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

BASE = "https://api-m.sandbox.paypal.com"

env = {}
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
if env.get("PAYPAL_ENV") != "SANDBOX":
    raise SystemExit("Stopping: PAYPAL_ENV must be SANDBOX")

creds = f'{env["PAYPAL_CLIENT_ID"]}:{env["PAYPAL_CLIENT_SECRET"]}'
token_request = urllib.request.Request(
    BASE + "/v1/oauth2/token",
    data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
    headers={"Authorization": "Basic " + base64.b64encode(creds.encode()).decode(),
             "Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(token_request) as response:
    token = json.load(response)["access_token"]

path = "/v1/customer/disputes"
if len(sys.argv) > 1:
    path += "/" + sys.argv[1]  # a dispute ID shows the full details

request = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + token})
try:
    with urllib.request.urlopen(request) as response:
        print(json.dumps(json.load(response), indent=2))
except urllib.error.HTTPError as err:
    print("FAILED:", err.code, err.read().decode())