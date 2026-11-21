"""
Telecom & Credit Card Bundle Reference Data (Unverified Placeholders)
=====================================================================
IMPORTANT:
Telecom plans (Jio, Airtel) and credit-card bundles (e.g. HDFC Infinia SmartBuy)
CANNOT be automatically inferred from raw bank statement debits.
These are modeled as Plan nodes. An INCLUDES relationship is created ONLY after
the user explicitly selects and confirms their specific plan.

All entries here have is_verified: False, confidence: 'user_confirmation_required'.
DO NOT invent prices or inclusions; verify with official carrier terms.
"""

TELECOM_CREDIT_CARD_PLANS = [
    {
        "plan_id": "jio_fiber_postpaid_entertainment",
        "plan_name": "JioFiber Postpaid Entertainment Bonanza",
        "carrier_or_bank": "Reliance Jio",
        "tier": "postpaid_bundle",
        "bundled_services": ["disney_hotstar", "sony_liv", "zee5", "jiocinema_premium"],
        "is_verified": False,
        "confidence": "user_confirmation_required",
        "source_url": "TODO: fill link", # e.g. https://www.jio.com/fiber/en-in/plans
        "notes": "PLACEHOLDER: Requires user confirmation of active OTT add-on plan."
    },
    {
        "plan_id": "airtel_postpaid_infinity",
        "plan_name": "Airtel Postpaid Family / Infinity",
        "carrier_or_bank": "Bharti Airtel",
        "tier": "family_postpaid",
        "bundled_services": ["amazon_prime", "disney_hotstar"],
        "is_verified": False,
        "confidence": "user_confirmation_required",
        "source_url": "TODO: fill link", # e.g. https://www.airtel.in/postpaid/
        "notes": "PLACEHOLDER: Requires user confirmation of Airtel Thanks Platinum rewards claim."
    },
    {
        "plan_id": "hdfc_infinia_smartbuy",
        "plan_name": "HDFC Infinia Metal Credit Card",
        "carrier_or_bank": "HDFC Bank",
        "tier": "super_premium_card",
        "bundled_services": ["times_prime"],
        "is_verified": False,
        "confidence": "user_confirmation_required",
        "source_url": "TODO: fill link",
        "notes": "PLACEHOLDER: Requires user confirmation of active complimentary Times Prime membership."
    }
]
