"""
Bank Statement CSV Extractor
Auto-detects bank dialects (HDFC, SBI, ICICI, Axis, Kotak) and delimiter formats.
"""
import io
import pandas as pd
from typing import List, Dict, Any
from app.services.normalizer import parse_date, parse_amount, clean_descriptor, detect_rail

class CSVExtractionError(Exception):
    pass

def extract_transactions_from_csv(csv_bytes: bytes) -> List[Dict[str, Any]]:
    """Parses CSV bytes into normalized transaction records."""
    if not csv_bytes:
        raise CSVExtractionError("CSV file is empty.")

    # Decode content
    try:
        text = csv_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = csv_bytes.decode("latin-1")
        except UnicodeDecodeError:
            text = csv_bytes.decode("cp1252", errors="ignore")

    # Detect delimiter
    sample = text[:2048]
    delimiter = ","
    if "\t" in sample and sample.count("\t") > sample.count(","):
        delimiter = "\t"
    elif ";" in sample and sample.count(";") > sample.count(","):
        delimiter = ";"

    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter)
    except Exception as e:
        raise CSVExtractionError(f"Failed to parse CSV format: {str(e)}")

    if df.empty:
        raise CSVExtractionError("The CSV file contains zero rows.")

    # Resolve column names across bank dialects
    cols = {str(c).strip().lower(): c for c in df.columns}

    date_col = next((cols[k] for k in [
        "date", "transaction date", "txn date", "value date", "valuedate",
        "transaction timestamp", "trans date", "timestamp", "time"
    ] if k in cols), None)

    desc_col = next((cols[k] for k in [
        "descriptor", "description", "narration", "particulars",
        "remarks", "details", "txn narration", "transaction narration"
    ] if k in cols), None)

    amt_col = next((cols[k] for k in [
        "amount", "debit", "withdrawal", "txn amount", "amount (inr)",
        "txn_amount", "transaction amount", "dr", "withdrawals"
    ] if k in cols), None)

    ref_col = next((cols[k] for k in [
        "ref", "reference", "chq/ref no.", "utr", "txn id", "id", "txnid",
        "cheque no", "ref no"
    ] if k in cols), None)

    if not date_col or not desc_col or not amt_col:
        raise CSVExtractionError(
            f"CSV is missing required banking columns (Date, Narration, Amount/Debit). Found: {list(df.columns)}"
        )

    transactions = []
    for idx, row in df.iterrows():
        raw_date = str(row[date_col]).strip()
        iso_date = parse_date(raw_date)
        if not iso_date:
            continue

        raw_desc = str(row[desc_col]).strip()
        if not raw_desc or raw_desc.lower() in ["nan", "null"]:
            continue

        amt_val, dir_val = parse_amount(row[amt_col])
        if amt_val <= 0:
            continue

        ref_val = str(row[ref_col]).strip() if ref_col and pd.notna(row[ref_col]) else ""

        transactions.append({
            "id": f"CSV_TX_{idx+1}",
            "date": iso_date,
            "descriptor": raw_desc,
            "cleaned_descriptor": clean_descriptor(raw_desc),
            "amount": amt_val,
            "type": dir_val,
            "ref": ref_val,
            "payment_rail": detect_rail(raw_desc, ref_val)
        })

    if not transactions:
        raise CSVExtractionError("No valid debit transactions could be parsed from the CSV file.")

    return transactions

