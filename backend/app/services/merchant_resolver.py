"""
Merchant Resolution Service
Resolves raw transaction descriptors to canonical merchant identities,
unwraps intermediate payment aggregators (Razorpay, BillDesk, Paytm, Cashfree),
and retrieves corporate hierarchies and cancellation workflows.
"""
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.services.normalizer import detect_aggregator, detect_rail, clean_descriptor

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from reference_data import REFERENCE_MERCHANTS, PARENT_COMPANIES, PAYMENT_MECHANISMS

class MerchantResolver:
    _cached_regexes = []

    @classmethod
    def _get_regexes(cls):
        if not cls._cached_regexes:
            for m in REFERENCE_MERCHANTS:
                patterns = [re.compile(p, re.IGNORECASE) for p in m.get("descriptors", [])]
                cls._cached_regexes.append((m, patterns))
        return cls._cached_regexes

    @classmethod
    def resolve(
        cls,
        raw_descriptor: str,
        ref_str: str = "",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Deterministically resolves raw banking descriptor to a canonical merchant.
        Unwraps payment aggregators and extracts corporate parents.
        """
        aggregator = detect_aggregator(raw_descriptor)
        rail = detect_rail(raw_descriptor, ref_str)
        cleaned = clean_descriptor(raw_descriptor)

        # 1. Direct Regex Match over Reference Knowledge Base
        matched_merchant = None
        for m_info, compiled_list in cls._get_regexes():
            for regex in compiled_list:
                if regex.search(raw_descriptor):
                    matched_merchant = m_info
                    break
            if matched_merchant:
                break

        # 2. Aggregator Unwrapping Fallback
        # If descriptor is "POS 4921*RAZORPAY*CUREFIT HEALTHCARE BLR", strip aggregator/terminal noise and retry
        if not matched_merchant:
            stripped = re.sub(r"POS\s+\d+\*?", "", raw_descriptor, flags=re.IGNORECASE)
            if aggregator:
                stripped = re.sub(rf"\b{aggregator}\*?", "", stripped, flags=re.IGNORECASE)
            stripped = stripped.strip()

            for m_info, compiled_list in cls._get_regexes():
                for regex in compiled_list:
                    if regex.search(stripped):
                        matched_merchant = m_info
                        break
                if matched_merchant:
                    break

            # If still not matched, check brand token affinity
            if not matched_merchant:
                cleaned_tokens = set(clean_descriptor(stripped).split())
                for m_info, compiled_list in cls._get_regexes():
                    # Extract significant words from merchant name and descriptor patterns
                    m_tokens = set()
                    for p in m_info.get("descriptors", []):
                        for word in re.findall(r"[A-Za-z]{4,}", p):
                            if word.upper() not in ["PVT", "LTD", "SUBS", "BILL", "HELPPAY", "MEMBERSHIP", "RECURRING", "AUTOPAY", "MEDIA", "INDIA", "SERVICES"]:
                                m_tokens.add(word.upper())
                    
                    if cleaned_tokens.intersection(m_tokens):
                        matched_merchant = m_info
                        break

        # 3. Database Fallback (if custom merchants exist in DB)
        if not matched_merchant and db:
            db_merchants = db.query(Merchant).all()
            for db_m in db_merchants:
                for pat in (db_m.descriptor_regexes or []):
                    if re.search(pat, raw_descriptor, re.IGNORECASE):
                        matched_merchant = {
                            "id": db_m.id,
                            "name": db_m.brand_name,
                            "category": db_m.category,
                            "parent": db_m.parent_company,
                            "official_website": db_m.domain,
                            "default_mechanism": db_m.default_mechanism,
                            "support_email": db_m.support_email,
                            "grievance_email": db_m.grievance_email,
                            "cancellation_pitfall": db_m.cancellation_pitfall
                        }
                        break
                if matched_merchant:
                    break

        # 4. Construct Structured Resolution Payload
        if matched_merchant:
            mech_code = matched_merchant.get("default_mechanism", rail)
            mech_details = PAYMENT_MECHANISMS.get(mech_code, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])
            
            return {
                "is_recognized": True,
                "merchant_id": matched_merchant["id"],
                "merchant_name": matched_merchant["name"],
                "category": matched_merchant["category"],
                "parent_name": matched_merchant.get("parent", "Independent / Unmapped"),
                "aggregator": aggregator,
                "payment_rail": rail,
                "mechanism_name": mech_details["name"],
                "cancellation_steps": mech_details["cancellation_steps"],
                "pitfall": matched_merchant.get("cancellation_pitfall", ""),
                "support_email": matched_merchant.get("support_email", ""),
                "grievance_email": matched_merchant.get("grievance_email", ""),
                "official_website": matched_merchant.get("official_website", "")
            }

        # Unrecognised Descriptor Fallback (Never Hallucinates)
        return {
            "is_recognized": False,
            "merchant_id": None,
            "merchant_name": f"Unrecognised: {cleaned[:30]}",
            "category": "Uncategorized Subscription",
            "parent_name": "Independent / Unmapped",
            "aggregator": aggregator,
            "payment_rail": rail,
            "mechanism_name": PAYMENT_MECHANISMS.get(rail, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])["name"],
            "cancellation_steps": PAYMENT_MECHANISMS.get(rail, PAYMENT_MECHANISMS["DIRECT_MERCHANT"])["cancellation_steps"],
            "pitfall": "Verify merchant terms and check banking application for mandate revocation.",
            "support_email": "",
            "grievance_email": "",
            "official_website": ""
        }
