"""
Merchants API Router (v1)
Provides merchant descriptor resolution, aggregator unwrapping, and merchant catalog inspection.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.db import get_db
from app.models.merchant import Merchant
from app.services.merchant_resolver import MerchantResolver

router = APIRouter(prefix="/merchants", tags=["Merchants"])

class ResolveDescriptorRequest(BaseModel):
    descriptor: str
    ref: Optional[str] = ""

class ResolveDescriptorResponse(BaseModel):
    is_recognized: bool
    merchant_id: Optional[str]
    merchant_name: str
    category: str
    parent_name: Optional[str]
    aggregator: Optional[str]
    payment_rail: str
    mechanism_name: str
    cancellation_steps: List[str]
    pitfall: str
    support_email: Optional[str] = ""
    grievance_email: Optional[str] = ""
    official_website: Optional[str] = ""

@router.post("/resolve", response_model=ResolveDescriptorResponse)
def resolve_descriptor(
    req: ResolveDescriptorRequest,
    db: Session = Depends(get_db)
):
    """
    Resolves raw bank statement or SMS descriptors to verified merchant identities.
    Unwraps third-party payment gateways (Razorpay, BillDesk, Paytm, Cashfree).
    """
    if not req.descriptor.strip():
        raise HTTPException(status_code=400, detail="Descriptor cannot be empty.")
    
    return MerchantResolver.resolve(req.descriptor, req.ref or "", db=db)

@router.get("")
def list_merchants(
    category: Optional[str] = None,
    parent: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists merchants cataloged in the knowledge base."""
    query = db.query(Merchant)
    if category:
        query = query.filter(Merchant.category.ilike(f"%{category}%"))
    if parent:
        query = query.filter(Merchant.parent_company.ilike(f"%{parent}%"))
    if search:
        query = query.filter(
            (Merchant.brand_name.ilike(f"%{search}%")) |
            (Merchant.category.ilike(f"%{search}%")) |
            (Merchant.parent_company.ilike(f"%{search}%"))
        )
    
    merchants = query.order_by(Merchant.brand_name.asc()).all()
    return [
        {
            "id": m.id,
            "brand_name": m.brand_name,
            "category": m.category,
            "parent_company": m.parent_company,
            "default_mechanism": m.default_mechanism,
            "domain": m.domain,
            "support_email": m.support_email,
            "descriptor_patterns_count": len(m.descriptor_regexes or [])
        }
        for m in merchants
    ]

@router.get("/{merchant_id}")
def get_merchant_detail(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full merchant details including cancellation guidance and legal contacts."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found in reference catalog.")
    
    return {
        "id": merchant.id,
        "brand_name": merchant.brand_name,
        "legal_name": merchant.legal_name,
        "category": merchant.category,
        "parent_company": merchant.parent_company,
        "default_mechanism": merchant.default_mechanism,
        "domain": merchant.domain,
        "support_email": merchant.support_email,
        "grievance_email": merchant.grievance_email,
        "cancellation_pitfall": merchant.cancellation_pitfall,
        "descriptor_regexes": merchant.descriptor_regexes
    }

