"""
Subscription Management & Portfolio Aggregation Service
Computes financial summaries, category allocations, corporate exposure,
and savings simulator projections.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.mandate import Mandate
from app.services.anomaly_engine import AnomalyEngine

class SubscriptionManager:
    @classmethod
    def get_portfolio_overview(cls, user_id: str, db: Session) -> Dict[str, Any]:
        """Calculates comprehensive portfolio metrics, category spend, and corporate footprint."""
        mandates = db.query(Mandate).filter(
            Mandate.user_id == user_id,
            Mandate.status == "ACTIVE"
        ).all()

        if not mandates:
            return {
                "hero_metrics": {
                    "total_active_mandates": 0,
                    "annual_committed_total": 0.0,
                    "monthly_equivalent": 0.0,
                    "potential_savings": 0.0,
                    "flagged_issues_count": 0
                },
                "category_breakdown": {},
                "corporate_footprint": {},
                "payment_rail_breakdown": {},
                "duplicates": []
            }

        total_annual = sum(float(m.annual_committed_cost) for m in mandates)
        potential_savings = sum(float(m.annual_committed_cost) for m in mandates if m.flag != "HEALTHY")
        flagged_count = sum(1 for m in mandates if m.flag != "HEALTHY")

        # 1. Category Breakdown
        categories: Dict[str, Dict[str, Any]] = {}
        for m in mandates:
            cat = m.category or "Uncategorized Subscription"
            if cat not in categories:
                categories[cat] = {"name": cat, "annual_cost": 0.0, "mandates_count": 0}
            categories[cat]["annual_cost"] += float(m.annual_committed_cost)
            categories[cat]["mandates_count"] += 1

        for c in categories.values():
            c["annual_cost"] = round(c["annual_cost"], 2)
            c["percentage_of_total"] = round((c["annual_cost"] / total_annual) * 100.0, 1) if total_annual > 0 else 0.0

        # 2. Corporate Footprint (Parent Companies)
        parents: Dict[str, Dict[str, Any]] = {}
        for m in mandates:
            p_name = m.parent_name or "Independent / Unmapped"
            if p_name not in parents:
                parents[p_name] = {"parent": p_name, "annual_cost": 0.0, "services": []}
            parents[p_name]["annual_cost"] += float(m.annual_committed_cost)
            if m.merchant_name not in parents[p_name]["services"]:
                parents[p_name]["services"].append(m.merchant_name)

        for p in parents.values():
            p["annual_cost"] = round(p["annual_cost"], 2)
            p["percentage_of_total"] = round((p["annual_cost"] / total_annual) * 100.0, 1) if total_annual > 0 else 0.0

        # 3. Payment Rails Breakdown
        rails: Dict[str, Dict[str, Any]] = {}
        for m in mandates:
            rail = m.mandate_type or "DIRECT_MERCHANT"
            if rail not in rails:
                rails[rail] = {"rail": rail, "annual_cost": 0.0, "count": 0}
            rails[rail]["annual_cost"] += float(m.annual_committed_cost)
            rails[rail]["count"] += 1

        for r in rails.values():
            r["annual_cost"] = round(r["annual_cost"], 2)

        # 4. Duplicate Subscriptions Check
        duplicates = AnomalyEngine.detect_duplicate_subscriptions(mandates)

        return {
            "hero_metrics": {
                "total_active_mandates": len(mandates),
                "annual_committed_total": round(total_annual, 2),
                "monthly_equivalent": round(total_annual / 12.0, 2),
                "potential_savings": round(potential_savings, 2),
                "flagged_issues_count": flagged_count
            },
            "category_breakdown": sorted(list(categories.values()), key=lambda x: -x["annual_cost"]),
            "corporate_footprint": sorted(list(parents.values()), key=lambda x: -x["annual_cost"]),
            "payment_rail_breakdown": sorted(list(rails.values()), key=lambda x: -x["annual_cost"]),
            "duplicates": duplicates
        }

