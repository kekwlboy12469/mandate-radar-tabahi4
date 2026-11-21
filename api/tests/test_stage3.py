"""
Stage 3 Automated Integration Test Suite
Validates Time-Windowed Fuzzy Deduplication, Aggregator Unwrapping,
Merchant Graph Resolution, and Merchant API Endpoints.
"""
from datetime import date
from fastapi.testclient import TestClient

from app.models.transaction import Transaction
from app.services.deduplication import DeduplicationService
from app.services.merchant_resolver import MerchantResolver
from main import app

def test_deduplication_exact_reference():
    existing_tx = Transaction(
        id="tx_1",
        user_id="user_test",
        amount=499.0,
        transaction_date=date(2026, 1, 15),
        raw_descriptor="NETFLIX MUMBAI",
        ref_number="UTR9482014"
    )
    
    # Candidate with same UTR reference and amount, even with different descriptor wording
    candidate = {
        "id": "cand_1",
        "date": "2026-01-15",
        "amount": 499.0,
        "descriptor": "NETFLIX ENTERTAINMENT SERVICES",
        "ref": "UTR9482014"
    }
    
    is_dup, matched, score, reason = DeduplicationService.is_duplicate(candidate, [existing_tx])
    assert is_dup is True
    assert reason == "EXACT_REFERENCE_MATCH"
    assert score == 1.0

def test_deduplication_time_window_fuzzy():
    # Existing statement recorded on Jan 15
    existing_tx = Transaction(
        id="tx_netflix",
        user_id="user_test",
        amount=149.0,
        transaction_date=date(2026, 1, 15),
        raw_descriptor="GOOGLE*YOUTUBE G.CO/HELPPAY",
        ref_number=""
    )
    
    # Candidate arrives from SMS alert recorded on Jan 16 (+1 day), slightly different string
    candidate = {
        "id": "cand_sms",
        "date": "2026-01-16",
        "amount": 149.0,
        "descriptor": "GOOGLE SERVICES YOUTUBE PREMIUM",
        "ref": ""
    }
    
    is_dup, matched, score, reason = DeduplicationService.is_duplicate(candidate, [existing_tx])
    assert is_dup is True
    assert "TIME_WINDOW_FUZZY_MATCH" in reason
    assert matched.id == "tx_netflix"

def test_deduplication_non_duplicate():
    existing_tx = Transaction(
        id="tx_netflix",
        user_id="user_test",
        amount=499.0,
        transaction_date=date(2026, 1, 15),
        raw_descriptor="NETFLIX MUMBAI",
        ref_number=""
    )
    
    # Different amount (₹649 vs ₹499)
    cand_diff_amt = {
        "id": "cand_diff",
        "date": "2026-01-15",
        "amount": 649.0,
        "descriptor": "NETFLIX MUMBAI"
    }
    is_dup, _, _, _ = DeduplicationService.is_duplicate(cand_diff_amt, [existing_tx])
    assert is_dup is False
    
    # Outside time window (15 days later)
    cand_diff_date = {
        "id": "cand_date",
        "date": "2026-01-30",
        "amount": 499.0,
        "descriptor": "NETFLIX MUMBAI"
    }
    is_dup, _, _, _ = DeduplicationService.is_duplicate(cand_diff_date, [existing_tx])
    assert is_dup is False

def test_merchant_resolver_direct_and_aggregator():
    # 1. Direct verified match
    res_yt = MerchantResolver.resolve("GOOGLE*YOUTUBE G.CO/HELPPAY")
    assert res_yt["is_recognized"] is True
    assert res_yt["merchant_id"] == "youtube_premium"
    assert res_yt["parent_name"] == "Alphabet Inc."
    
    # 2. Aggregator unwrapping (Razorpay prefix in bank memo)
    res_agg = MerchantResolver.resolve("POS 4921*RAZORPAY*CUREFIT HEALTHCARE BLR")
    assert res_agg["is_recognized"] is True
    assert res_agg["merchant_id"] == "cult_fit"
    assert res_agg["aggregator"] == "RAZORPAY"
    assert res_agg["payment_rail"] == "CARD_SI" or res_agg["payment_rail"] == "DIRECT_MERCHANT"
    
    # 3. Unrecognized descriptor check (Never hallucinate)
    res_unk = MerchantResolver.resolve("RANDOM BAKERY AND CHAI STALL #9281")
    assert res_unk["is_recognized"] is False
    assert res_unk["merchant_id"] is None
    assert "Unrecognised" in res_unk["merchant_name"]

def test_merchants_api():
    client = TestClient(app)
    
    # 1. Resolve descriptor endpoint
    res = client.post("/api/v1/merchants/resolve", json={
        "descriptor": "AMZN PRIME IN*849204"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_recognized"] is True
    assert data["merchant_id"] == "amazon_prime"
    assert data["parent_name"] == "Amazon.com Inc."
    
    # 2. List merchants
    list_res = client.get("/api/v1/merchants?category=Entertainment")
    assert list_res.status_code == 200
    merchants = list_res.json()
    assert len(merchants) > 0
    assert any(m["id"] == "netflix_india" for m in merchants)
    
    # 3. Single merchant detail
    detail_res = client.get("/api/v1/merchants/netflix_india")
    assert detail_res.status_code == 200
    det = detail_res.json()
    assert det["brand_name"] == "Netflix India"
    assert "cancellation_pitfall" in det

if __name__ == "__main__":
    test_deduplication_exact_reference()
    print("Deduplication (Exact Reference): OK")
    test_deduplication_time_window_fuzzy()
    print("Deduplication (Time-Window Fuzzy Matching): OK")
    test_deduplication_non_duplicate()
    print("Deduplication (Non-Duplicate Discrimination): OK")
    test_merchant_resolver_direct_and_aggregator()
    print("Merchant Resolver (Direct & Aggregator Unwrapping): OK")
    test_merchants_api()
    print("Merchants API Endpoints: OK")
    print("STAGE 3 VERIFICATION COMPLETE: ALL TESTS PASSED!")

