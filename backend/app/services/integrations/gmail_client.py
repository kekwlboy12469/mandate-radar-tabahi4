"""
Engine 1: Official Gmail OAuth 2.0 Client & Incremental Sync Engine
Implements users.history.list incremental synchronization and MIME parsing.
Scope strictly restricted to: https://www.googleapis.com/auth/gmail.readonly
"""
import urllib.parse
import json
import base64
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os

from app.core.config import settings
from app.services.integrations.gmail_sync import GmailSyncService

class GmailClient:
    """
    Manages OAuth 2.0 lifecycle and incremental synchronization with the official Gmail API v1.
    """
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

    DEFAULT_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

    @classmethod
    def get_client_credentials(cls) -> Tuple[str, str, str]:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "mock-client-id.apps.googleusercontent.com")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "mock-client-secret")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/gmail/callback")
        return client_id, client_secret, redirect_uri

    @classmethod
    def generate_authorization_url(cls, state: str) -> str:
        """
        Builds Google OAuth 2.0 consent URL requesting offline access (refresh token)
        and read-only permissions for financial invoices.
        """
        client_id, _, redirect_uri = cls.get_client_credentials()
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": cls.DEFAULT_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        return f"{cls.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code_for_tokens(cls, code: str) -> Dict[str, Any]:
        """
        Exchanges authorization code for access and refresh tokens.
        """
        client_id, client_secret, redirect_uri = cls.get_client_credentials()
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        # If running in mock / test environment with mock code:
        if code.startswith("mock_code") or client_id.startswith("mock"):
            return {
                "access_token": f"ya29.mock_access_{code}",
                "refresh_token": f"1//mock_refresh_{code}",
                "expires_in": 3600,
                "scope": cls.DEFAULT_SCOPE,
                "token_type": "Bearer"
            }

        resp = requests.post(cls.GOOGLE_TOKEN_URL, data=data, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"Failed to exchange OAuth code: {resp.text}")
        return resp.json()

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        """
        Obtains a fresh access token using the stored encrypted refresh token.
        """
        client_id, client_secret, _ = cls.get_client_credentials()
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        if refresh_token.startswith("1//mock"):
            return {
                "access_token": f"ya29.mock_refreshed_access_{datetime.utcnow().timestamp()}",
                "expires_in": 3600
            }

        resp = requests.post(cls.GOOGLE_TOKEN_URL, data=data, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"Token refresh failed: {resp.text}")
        return resp.json()

    @classmethod
    def revoke_token(cls, token: str) -> bool:
        """
        Revokes OAuth access on Google's authorization server.
        """
        if token.startswith("mock") or token.startswith("ya29.mock"):
            return True
        try:
            resp = requests.post(
                cls.GOOGLE_REVOKE_URL,
                params={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_user_profile(cls, access_token: str) -> Dict[str, Any]:
        """
        Fetches user email address and current mailbox historyId.
        """
        if access_token.startswith("ya29.mock"):
            return {
                "emailAddress": "user@gmail.com",
                "messagesTotal": 1420,
                "threadsTotal": 850,
                "historyId": "992140"
            }

        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(f"{cls.GMAIL_API_BASE}/profile", headers=headers, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"Could not fetch Gmail profile: {resp.text}")
        return resp.json()

    @classmethod
    def extract_mime_body(cls, payload: Dict[str, Any]) -> str:
        """
        Recursively extracts plaintext or HTML body from Gmail MIME structure.
        """
        body_text = ""
        mime_type = payload.get("mimeType", "")
        parts = payload.get("parts", [])

        if "body" in payload and payload["body"].get("data"):
            data = payload["body"]["data"]
            try:
                decoded = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")
                body_text += decoded
            except Exception:
                pass

        for part in parts:
            p_mime = part.get("mimeType", "")
            if p_mime in ("text/plain", "text/html"):
                if part.get("body", {}).get("data"):
                    try:
                        dec = base64.urlsafe_b64decode(part["body"]["data"].encode("ASCII")).decode("utf-8", errors="replace")
                        body_text += "\n" + dec
                    except Exception:
                        pass
            elif "parts" in part:
                body_text += "\n" + cls.extract_mime_body(part)

        return body_text

    @classmethod
    def sync_financial_emails(
        cls,
        access_token: str,
        start_history_id: Optional[str] = None,
        max_messages: int = 50
    ) -> Dict[str, Any]:
        """
        Performs incremental or initial financial email ingestion.
        Returns extracted transactions, updated historyId, and execution metrics.
        """
        # If in mock mode, return deterministic financial email batches
        if access_token.startswith("ya29.mock"):
            mock_invoices = [
                {
                    "id": "msg_netflix_01",
                    "subject": "Your Netflix Invoice for November 2026",
                    "sender": "info@mailer.netflix.com",
                    "date": "2026-11-15",
                    "body": "Hi Arun,\nPlan: Premium Ultra HD\nTotal for this month: ₹649.00\nPayment Method: UPI AutoPay (UMN 9b1deb4d3b7d4e899b82142a781d4512)\nInvoice ID: INV-NET-99182374"
                },
                {
                    "id": "msg_google_02",
                    "subject": "Google Workspace Monthly Receipt",
                    "sender": "payments-noreply@google.com",
                    "date": "2026-11-12",
                    "body": "Subtotal: ₹1,650.00 debited via HDFC Card ending 4821. Invoice: GOOG-WS-881239"
                },
                {
                    "id": "msg_spotify_03",
                    "subject": "Your Spotify Premium Receipt",
                    "sender": "no-reply@spotify.com",
                    "date": "2026-11-10",
                    "body": "Receipt Number: 9812401824\nAmount paid: ₹149.00\nUPI Ref 429104829102"
                }
            ]
            parsed_results = []
            for item in mock_invoices:
                p = GmailSyncService.parse_email(
                    subject=item["subject"],
                    sender=item["sender"],
                    body=item["body"]
                )
                p["source_message_id"] = item["id"]
                parsed_results.append(p)

            return {
                "sync_mode": "MOCK_INCREMENTAL" if start_history_id else "MOCK_FULL",
                "messages_scanned": len(mock_invoices),
                "financial_records": parsed_results,
                "latest_history_id": "993500",
                "has_more": False
            }

        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 1. Try Incremental History Sync if historyId is available
        message_ids = set()
        latest_history_id = start_history_id

        if start_history_id:
            try:
                hist_url = f"{cls.GMAIL_API_BASE}/history?startHistoryId={start_history_id}&historyTypes=messageAdded&maxResults={max_messages}"
                resp = requests.get(hist_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    hist_data = resp.json()
                    latest_history_id = hist_data.get("historyId", start_history_id)
                    for h_record in hist_data.get("history", []):
                        for m_added in h_record.get("messagesAdded", []):
                            msg_obj = m_added.get("message", {})
                            if msg_obj.get("id"):
                                message_ids.add(msg_obj["id"])
                elif resp.status_code == 404:
                    # HistoryId expired (Gmail stores history for ~30 days) -> fallback to query search
                    start_history_id = None
            except Exception:
                start_history_id = None

        # 2. Query Search fallback (or initial sync)
        if not start_history_id or not message_ids:
            query = GmailSyncService.FINANCIAL_QUERY
            search_url = f"{cls.GMAIL_API_BASE}/messages?q={urllib.parse.quote(query)}&maxResults={max_messages}"
            resp = requests.get(search_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                raise ValueError(f"Gmail search query failed: {resp.text}")
            s_data = resp.json()
            for m in s_data.get("messages", []):
                message_ids.add(m["id"])
            
            # Fetch current profile to get latest historyId
            profile = cls.get_user_profile(access_token)
            latest_history_id = profile.get("historyId", "1")

        # 3. Retrieve and parse full messages
        financial_records = []
        for msg_id in message_ids:
            try:
                m_url = f"{cls.GMAIL_API_BASE}/messages/{msg_id}?format=full"
                m_resp = requests.get(m_url, headers=headers, timeout=10)
                if m_resp.status_code != 200:
                    continue
                m_data = m_resp.json()
                
                # Extract headers
                h_dict = {}
                for h in m_data.get("payload", {}).get("headers", []):
                    h_dict[h["name"].lower()] = h["value"]
                
                subject = h_dict.get("subject", "")
                sender = h_dict.get("from", "")
                body = cls.extract_mime_body(m_data.get("payload", {}))
                
                parsed = GmailSyncService.parse_email(
                    subject=subject,
                    sender=sender,
                    body=body
                )
                if parsed.get("is_financial"):
                    parsed["source_message_id"] = msg_id
                    financial_records.append(parsed)
            except Exception:
                continue

        return {
            "sync_mode": "INCREMENTAL" if start_history_id else "FULL",
            "messages_scanned": len(message_ids),
            "financial_records": financial_records,
            "latest_history_id": latest_history_id,
            "has_more": False
        }

