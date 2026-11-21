"""
Subscriptions & Intelligence API Router (v1)
Provides portfolio overview, category allocations, corporate spend footprint,
and anomaly resolution.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.core.db import get_db
from app.models.user import User
from app.models.mandate import Mandate
from app.api.v1.auth import get_current_user
from app.services.subscription_manager import SubscriptionManager

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/overview")
def get_subscription_portfolio_overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full portfolio analytics, category breakdown, and corporate parent exposure."""
    return SubscriptionManager.get_portfolio_overview(user.id, db)

@router.get("/anomalies")
def list_subscription_anomalies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all active commitments flagged with price creep, trial traps, or dormancy."""
    mandates = db.query(Mandate).filter(
        Mandate.user_id == user.id,
        Mandate.status == "ACTIVE",
        Mandate.flag != "HEALTHY"
    ).order_by(Mandate.annual_committed_cost.desc()).all()

    anomalies = []
    for m in mandates:
        anomalies.append({
            "mandate_id": m.id,
            "merchant_name": m.merchant_name,
            "category": m.category,
            "flag": m.flag,
            "flag_reason": m.flag_reason,
            "latest_amount": float(m.latest_amount),
            "cadence": m.cadence,
            "annual_committed_cost": float(m.annual_committed_cost),
            "savings_if_cancelled": float(m.annual_committed_cost)
        })

    return {
        "count": len(anomalies),
        "total_potential_savings": round(sum(a["annual_committed_cost"] for a in anomalies), 2),
        "anomalies": anomalies
    }

@router.post("/{mandate_id}/dismiss-flag")
def dismiss_mandate_flag(
    mandate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows user to acknowledge a price hike or change and reset the status to HEALTHY."""
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id, Mandate.user_id == user.id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate.flag = "HEALTHY"
    mandate.flag_reason = "Flag acknowledged and dismissed by user."
    db.commit()
    return {"success": True, "mandate_id": mandate_id, "flag": "HEALTHY"}

