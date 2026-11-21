"""
Multi-Source Time-Windowed Fuzzy Deduplication Service
Prevents double-counting when transactions arrive across overlapping sources (SMS, Statement PDF, CSV, Gmail).
"""
import difflib
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from app.models.transaction import Transaction
from app.services.normalizer import clean_descriptor

class DeduplicationService:
    @staticmethod
    def _text_similarity(desc_a: str, desc_b: str) -> float:
        """Calculates combined token set overlap and sequence similarity."""
        clean_a = clean_descriptor(desc_a).upper()
        clean_b = clean_descriptor(desc_b).upper()

        if not clean_a or not clean_b:
            return 0.0

        if clean_a == clean_b:
            return 1.0

        tokens_a = set(clean_a.split())
        tokens_b = set(clean_b.split())

        # Token Jaccard similarity
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Sequence matcher ratio
        seq_ratio = difflib.SequenceMatcher(None, clean_a, clean_b).ratio()

        # Weighted score favoring token overlap
        return (jaccard * 0.6) + (seq_ratio * 0.4)

    @classmethod
    def is_duplicate(
        cls,
        candidate: Dict[str, Any],
        existing_records: List[Transaction],
        tolerance_days: int = 2
    ) -> Tuple[bool, Optional[Transaction], float, str]:
        """
        Determines if a candidate transaction is a duplicate of any existing record.
        Returns: (is_duplicate: bool, matched_record, confidence_score, reason)
        """
        cand_amt = float(candidate["amount"])
        cand_date_str = candidate["date"]
        cand_date = datetime.strptime(cand_date_str[:10], "%Y-%m-%d").date() if isinstance(cand_date_str, str) else cand_date_str
        cand_ref = candidate.get("ref", "").strip().upper()
        cand_desc = candidate.get("descriptor", "")

        for ex in existing_records:
            # 1. Exact Reference Match (UTR, UPI Reference, Cheque No)
            ex_ref = (ex.ref_number or "").strip().upper()
            if cand_ref and ex_ref and cand_ref == ex_ref and abs(cand_amt - float(ex.amount)) < 0.01:
                return True, ex, 1.0, "EXACT_REFERENCE_MATCH"

            # 2. Amount Equality Check (within 1 paisa)
            if abs(cand_amt - float(ex.amount)) >= 0.01:
                continue

            # 3. Temporal Window Check (+/- tolerance_days)
            ex_date = ex.transaction_date
            if isinstance(ex_date, str):
                ex_date = datetime.strptime(ex_date[:10], "%Y-%m-%d").date()
            date_diff = abs((cand_date - ex_date).days)
            if date_diff > tolerance_days:
                continue

            # 4. Descriptor Similarity Check
            similarity = cls._text_similarity(cand_desc, ex.raw_descriptor)
            
            # Check for high-affinity brand token match (e.g. both contain "NETFLIX" or "YOUTUBE")
            tokens_cand = set(clean_descriptor(cand_desc).split())
            tokens_ex = set(clean_descriptor(ex.raw_descriptor).split())
            common_tokens = tokens_cand.intersection(tokens_ex)
            
            # If they share significant brand tokens or similarity is high (>0.60)
            if similarity >= 0.60 or any(len(t) >= 5 for t in common_tokens):
                return True, ex, round(similarity, 3), f"TIME_WINDOW_FUZZY_MATCH (dt={date_diff}d, score={similarity:.2f})"

        return False, None, 0.0, "UNIQUE"

    @classmethod
    def filter_unique_transactions(
        cls,
        candidates: List[Dict[str, Any]],
        existing_records: List[Transaction]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partitions candidate transactions into unique vs duplicates.
        Returns: (unique_list, duplicates_list)
        """
        unique: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []
        all_pool = list(existing_records)

        for cand in candidates:
            is_dup, matched_tx, score, reason = cls.is_duplicate(cand, all_pool)
            if is_dup:
                dup_record = cand.copy()
                dup_record["matched_existing_id"] = matched_tx.id
                dup_record["dedupe_score"] = score
                dup_record["dedupe_reason"] = reason
                duplicates.append(dup_record)
            else:
                unique.append(cand)
                # Add to temporary pool so intra-batch duplicates are also caught
                dummy_tx = Transaction(
                    id=cand.get("id", "batch_tmp"),
                    user_id=getattr(all_pool[0], "user_id", "") if all_pool else "",
                    amount=cand["amount"],
                    transaction_date=datetime.strptime(cand["date"][:10], "%Y-%m-%d").date() if isinstance(cand["date"], str) else cand["date"],
                    raw_descriptor=cand["descriptor"],
                    ref_number=cand.get("ref", "")
                )
                all_pool.append(dummy_tx)

        return unique, duplicates

