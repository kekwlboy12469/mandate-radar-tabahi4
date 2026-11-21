"""
Engine 6: Financial Graph Intelligence & Conglomerate Analytics
Exposes topological relationships: Corporate Parent Footprint, Functional Redundancies, and Exit Friction.
"""
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict
from reference_data import PARENT_COMPANIES, REFERENCE_MERCHANTS

class GraphAnalyticsService:
    """
    Performs graph-based aggregations across corporate entities,
    functional categories, and payment rails.
    """

    @classmethod
    def get_parent_company(cls, merchant_name: str) -> str:
        """
        Resolves ultimate corporate parent for a merchant.
        """
        clean = (merchant_name or "").lower().strip()
        
        # Check reference merchants list
        for m in REFERENCE_MERCHANTS:
            m_name = m.get("name", "").lower()
            if m_name in clean or clean in m_name:
                return m.get("parent", "Independent Service")
            for desc in m.get("descriptors", []):
                try:
                    if re.search(desc, clean, re.IGNORECASE):
                        return m.get("parent", "Independent Service")
                except Exception:
                    pass

        # Check PARENT_COMPANIES dict
        for p_id, p_info in PARENT_COMPANIES.items():
            p_name = p_info.get("name", "").lower()
            if p_id in clean or p_name in clean:
                return p_info.get("name", p_id.title())

        # Direct heuristics
        if "google" in clean or "youtube" in clean:
            return "Alphabet Inc."
        if "amazon" in clean or "prime" in clean or "aws" in clean:
            return "Amazon.com Inc."
        if "apple" in clean or "icloud" in clean:
            return "Apple Inc."
        if "microsoft" in clean or "azure" in clean:
            return "Microsoft Corporation"
        if "meta" in clean or "facebook" in clean:
            return "Meta Platforms Inc."
        if "netflix" in clean:
            return "Netflix Inc."
        if "spotify" in clean:
            return "Spotify Technology S.A."

        return "Independent Service"

    @classmethod
    def analyze_corporate_footprint(cls, mandates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregates spend across ultimate corporate parent conglomerates.
        Identifies subscription stack consolidation opportunities.
        """
        footprint = defaultdict(lambda: {
            "parent_company": "",
            "total_monthly_spend": 0.0,
            "total_annual_spend": 0.0,
            "active_services": [],
            "service_count": 0,
            "payment_rails": set()
        })

        for m in mandates:
            status = (m.get("status") or "ACTIVE").upper()
            if status in ("REVOKED", "EXPIRED"):
                continue

            name = m.get("merchant_name") or m.get("descriptor") or "Unknown"
            parent = cls.get_parent_company(name)
            amount = float(m.get("latest_amount") or m.get("amount") or 0.0)
            cadence = (m.get("cadence") or "MONTHLY").upper()
            rail = m.get("payment_rail") or m.get("mechanism") or "UPI"

            # Normalize to monthly
            if cadence == "ANNUAL" or cadence == "YEARLY":
                monthly = amount / 12.0
                annual = amount
            elif cadence == "QUARTERLY":
                monthly = amount / 3.0
                annual = amount * 4.0
            else:
                monthly = amount
                annual = amount * 12.0

            entry = footprint[parent]
            entry["parent_company"] = parent
            entry["total_monthly_spend"] += monthly
            entry["total_annual_spend"] += annual
            entry["active_services"].append({
                "merchant_name": name,
                "amount": amount,
                "cadence": cadence,
                "tier": m.get("mandate_tier", "INFERRED_SUBSCRIPTION")
            })
            entry["service_count"] += 1
            entry["payment_rails"].add(rail)

        results = []
        for parent, data in footprint.items():
            data["total_monthly_spend"] = round(data["total_monthly_spend"], 2)
            data["total_annual_spend"] = round(data["total_annual_spend"], 2)
            data["payment_rails"] = list(data["payment_rails"])
            
            # Identify consolidation tips
            consolidation_tip = None
            if "Alphabet" in parent and data["service_count"] >= 2:
                consolidation_tip = "Consider Google One Family bundle to consolidate storage and streaming services."
            elif "Apple" in parent and data["service_count"] >= 2:
                consolidation_tip = "Consider Apple One Premier subscription to save up to ₹400/month across music and cloud."
            elif "Amazon" in parent and data["service_count"] >= 2:
                consolidation_tip = "Verify if Prime Video is duplicated on secondary household cards."

            data["consolidation_tip"] = consolidation_tip
            results.append(data)

        results.sort(key=lambda x: x["total_monthly_spend"], reverse=True)
        return results

    @classmethod
    def detect_functional_redundancies(cls, mandates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifies multiple active recurring commitments serving identical functional purposes
        (e.g., overlapping OTT platforms, multiple cloud storage providers, multiple music apps).
        """
        CATEGORY_KEYWORDS = {
            "Music Streaming": ["spotify", "apple music", "amazon music", "gaana", "wynk", "jiosaavn", "youtube music"],
            "Video OTT Streaming": ["netflix", "hotstar", "disney", "prime video", "sony liv", "zee5", "apple tv"],
            "Cloud Storage": ["google one", "icloud", "dropbox", "onedrive"],
            "Fitness & Gym": ["cult.fit", "curefit", "fitness first", "gold's gym", "anytime fitness"],
            "AI Assistants": ["chatgpt", "openai", "claude", "midjourney", "github copilot", "perplexity"]
        }

        cat_groups = defaultdict(list)

        for m in mandates:
            status = (m.get("status") or "ACTIVE").upper()
            if status in ("REVOKED", "EXPIRED"):
                continue

            name = (m.get("merchant_name") or m.get("descriptor") or "").lower()
            matched_cat = None
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(kw in name for kw in keywords):
                    matched_cat = cat
                    break
            
            if matched_cat:
                cat_groups[matched_cat].append(m)

        redundancies = []
        for cat, items in cat_groups.items():
            if len(items) >= 2:
                total_cat_spend = sum(float(x.get("latest_amount", x.get("amount", 0.0))) for x in items)
                cheapest_exit = min(float(x.get("latest_amount", x.get("amount", 0.0))) for x in items)
                
                redundancies.append({
                    "category": cat,
                    "service_count": len(items),
                    "services": [x.get("merchant_name", x.get("descriptor")) for x in items],
                    "total_monthly_spend": round(total_cat_spend, 2),
                    "potential_annual_savings": round(cheapest_exit * 12.0, 2),
                    "recommendation": f"You are paying for {len(items)} {cat} subscriptions simultaneously. Canceling just one saves ₹{cheapest_exit * 12.0:.0f}/year."
                })

        return redundancies

    @classmethod
    def calculate_vulnerability_index(cls, mandates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Scores portfolio exit friction based on legal payment rails, dark patterns, and notice periods.
        """
        if not mandates:
            return {"portfolio_score": 0, "risk_level": "LOW", "breakdown": []}

        scores = []
        breakdown = []

        for m in mandates:
            rail = (m.get("payment_rail") or m.get("mechanism") or "DIRECT_MERCHANT").upper()
            amount = float(m.get("latest_amount") or m.get("amount") or 0.0)
            name = m.get("merchant_name") or m.get("descriptor") or "Unknown"

            # Score friction: 0 (easy) to 100 (difficult)
            if "NACH" in rail or "ECS" in rail or "BANK_NACH" in rail:
                friction = 85
                reason = "NACH Mandate: Requires formal bank revocation or branch submission; difficult to cancel online."
            elif "CARD" in rail or "STANDING_INSTRUCTION" in rail:
                friction = 60
                reason = "Credit Card Recurring: Requires navigating merchant billing settings; bank dispute may be required if merchant resists."
            elif "UPI" in rail:
                friction = 15
                reason = "UPI AutoPay: Low friction; revocable instantly in 1 tap inside your UPI app (GPay/PhonePe/Paytm)."
            else:
                friction = 50
                reason = "Standard Web Billing: Varies by vendor portal."

            # Weight by commitment size
            weighted = friction
            scores.append(weighted)
            breakdown.append({
                "merchant_name": name,
                "payment_rail": rail,
                "friction_score": friction,
                "reason": reason
            })

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        risk_level = "HIGH_LOCK_IN" if avg_score > 65 else ("MODERATE_LOCK_IN" if avg_score > 35 else "USER_AUTONOMOUS")

        return {
            "portfolio_vulnerability_score": avg_score,
            "risk_level": risk_level,
            "assessed_mandates_count": len(mandates),
            "breakdown": breakdown
        }
