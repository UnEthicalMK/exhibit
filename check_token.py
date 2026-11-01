import base64, json, urllib.request, urllib.parse, urllib.error
from pathlib import Path

env = {}
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')

if env.get("PAYPAL_ENV") != "SANDBOX":
    raise SystemExit("Stopping: PAYPAL_ENV must be SANDBOX")

creds = f'{env["PAYPAL_CLIENT_ID"]}:{env["PAYPAL_CLIENT_SECRET"]}'
request = urllib.request.Request(
    "https://api-m.sandbox.paypal.com/v1/oauth2/token",
    data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
    headers={
        "Authorization": "Basic " + base64.b64encode(creds.encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded",
    },
)
try:
    with urllib.request.urlopen(request) as response:
        body = json.load(response)
    print("OK: got an access token, expires in", body.get("expires_in"), "seconds")
except urllib.error.HTTPError as err:
    print("FAILED:", err.code, err.read().decode())