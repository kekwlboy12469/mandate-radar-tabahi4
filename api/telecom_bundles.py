"""
TELECOM & CREDIT CARD BUNDLE PLACEHOLDER DATA
=====================================================
IMPORTANT:
Telecom (Jio, Airtel) and credit-card bundles (e.g., plans bundled with Disney+ Hotstar or Netflix)
are NOT automatically inferable from a raw bank statement debit.
These are modeled as Plan nodes. An INCLUDES relationship is created ONLY after the user
explicitly selects and confirms their specific plan.
DO NOT invent prices or inclusions; fill and verify this file with official carrier terms.
"""

# PLACEHOLDER: Telecom & Credit Card Plan Definitions
TELECOM_CREDIT_CARD_PLANS = [
    {
        "plan_id": "jio_prepaid_annual_hotstar",
        "plan_name": "Jio Annual Entertainment Plan",
        "carrier_or_bank": "Reliance Jio",
        "bundled_services": ["disney_hotstar"],
        "is_verified": False,
        "source_url": "TODO: fill link", # e.g. https://www.jio.com/plans
        "notes": "PLACEHOLDER: Verify if active plan includes mobile or all-device Hotstar subscription."
    },
    {
        "plan_id": "airtel_postpaid_infinity",
        "plan_name": "Airtel Postpaid Family / Infinity",
        "carrier_or_bank": "Bharti Airtel",
        "bundled_services": ["amazon_prime", "disney_hotstar"],
        "is_verified": False,
        "source_url": "TODO: fill link",
        "notes": "PLACEHOLDER: Verify Airtel Thanks Platinum tier OTT bundle terms."
    },
    {
        "plan_id": "hdfc_infinia_smartbuy",
        "plan_name": "HDFC Infinia Credit Card",
        "carrier_or_bank": "HDFC Bank",
        "bundled_services": ["club_marriott"],
        "is_verified": False,
        "source_url": "TODO: fill link",
        "notes": "PLACEHOLDER: Verify complimentary memberships attached to card."
    }
]
