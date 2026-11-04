from .paypal_client import PayPalClient

# Field in PayPal's verify call -> header PayPal sends with every webhook
SIGNATURE_HEADERS = {
    "auth_algo": "paypal-auth-algo",
    "cert_url": "paypal-cert-url",
    "transmission_id": "paypal-transmission-id",
    "transmission_sig": "paypal-transmission-sig",
    "transmission_time": "paypal-transmission-time",
}


def verify_signature(paypal: PayPalClient, headers, event: dict, webhook_id: str) -> bool:
    """Ask PayPal whether this webhook really came from PayPal, for our webhook ID."""
    body = {field: headers.get(name) for field, name in SIGNATURE_HEADERS.items()}
    if not webhook_id or not all(body.values()):
        return False  # unsigned, or no webhook ID configured: reject without calling PayPal
    body["webhook_id"] = webhook_id
    body["webhook_event"] = event
    result = paypal.request("POST", "/v1/notifications/verify-webhook-signature", json=body)
    return result.get("verification_status") == "SUCCESS"