NOT_ACTIONS = {"self", "detail"}


def allowed_actions(dispute: dict) -> list[str]:
    """Actions PayPal allows right now, read from the dispute's HATEOAS links.

    Sorted, because PayPal doesn't return links in a fixed order.
    """
    return sorted(
        link["rel"]
        for link in dispute.get("links", [])
        if link.get("rel") not in NOT_ACTIONS
    )