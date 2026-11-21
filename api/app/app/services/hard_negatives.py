"""
Hard Negative Filtering Service
Distinguishes genuine recurring commitments from rapid retail orders,
food delivery bursts, and metered variable utility bills.
"""
import re
from typing import Optional, Dict, Any, List

HARD_NEGATIVE_PATTERNS = [
    {
        "category": "Quick Groceries",
        "patterns": [r"ZEPTO", r"BLINKIT", r"INSTAMART", r"BIGBASKET", r"DUNZO"],
        "reason": "Rapid non-subscription on-demand grocery orders."
    },
    {
        "category": "Food Delivery",
        "patterns": [r"SWIGGY\s+ORDER", r"ZOMATO\s+ORDER", r"EATS"],
        "reason": "On-demand food delivery purchases."
    },
    {
        "category": "Metered Utilities",
        "patterns": [r"ELECTRICITY", r"POWER\s+DISTRIBUTION", r"BESCOM", r"TATA\s+POWER", r"WATER\s+BOARD", r"IGL\s+GAS"],
        "reason": "Variable consumption-based utility charges."
    },
    {
        "category": "Ride Hailing",
        "patterns": [r"UBER\s+TRIP", r"OLA\s+CABS", r"RAPIDO"],
        "reason": "Ad-hoc ride hailing fares."
    }
]

class HardNegativeFilter:
    @classmethod
    def match(cls, descriptor: str) -> Optional[Dict[str, str]]:
        """Checks if descriptor matches known hard-negative retail or utility patterns."""
        desc_upper = descriptor.upper()
        for group in HARD_NEGATIVE_PATTERNS:
            for p in group["patterns"]:
                if re.search(p, desc_upper):
                    return {
                        "category": group["category"],
                        "reason": group["reason"]
                    }
        return None

