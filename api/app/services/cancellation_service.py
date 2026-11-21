"""
Engine 5 & Stage 10: Legal Mandate Revocation & Cancellation Assistance Service
Generates formal revocation notices compliant with RBI Master Directions and DPDP Act 2023.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from app.models.mandate import Mandate
from reference_data import ESCALATION_CHAIN

class CancellationService:
    """
    Assists users in terminating recurring mandates, revoking consent,
    and navigating statutory escalation trees.
    """

    @classmethod
    def generate_legal_notice(
        cls,
        mandate: Mandate,
        user_name: str = "Authorized Account Holder",
        account_mask: str = "**XXXX",
        reason: str = "Voluntary Revocation of Consent / Service Discontinuation"
    ) -> Dict[str, Any]:
        """
        Constructs formal, legally binding mandate cancellation notices for both
        Merchant Grievance Officer and Issuing Bank Nodal Officer.
        """
        today_str = date.today().strftime("%d-%B-%Y")
        ref_token = mandate.umn_or_umrn or mandate.id
        amt = float(mandate.latest_amount)

        # 1. Merchant Formal Notice & Email Draft
        merchant_email_subject = f"REVOCATION NOTICE: Immediate Cancellation of Auto-Debit Mandate - Ref {ref_token}"
        merchant_email_body = f"""To: {mandate.grievance_email or mandate.support_email or 'support@merchant.com'}
Cc: Grievance Officer
Date: {today_str}
Subject: {merchant_email_subject}

Dear Grievance Officer / Customer Support Team,

RE: FORMAL NOTICE OF WITHDRAWAL OF CONSENT AND IMMEDIATE REVOCATION OF AUTO-DEBIT MANDATE

I am writing as the registered account holder to formally notify you of the immediate revocation and cancellation of all recurring payment mandates, standing instructions, and auto-debit authorizations associated with my account.

MANDATE IDENTIFICATION DETAILS:
• Merchant / Service Name: {mandate.merchant_name}
• Mandate Reference / UMN / UMRN: {ref_token}
• Transaction Cadence: {mandate.cadence}
• Recurring Amount: INR {amt:,.2f}
• Account / Payment Identifier: {account_mask}
• Reason for Cancellation: {reason}

LEGAL BASIS & STATUTORY COMPLIANCE:
1. Pursuant to RBI Master Direction on Processing of e-Mandates for Recurring Transactions (RBI/2020-21/74), account holders possess an absolute statutory right to revoke recurring payment mandates at any time.
2. In accordance with Section 6 of the Digital Personal Data Protection Act, 2023 (DPDP Act), I hereby withdraw my consent for recurring automated financial debit processing against my financial accounts.
3. Under the Consumer Protection (E-Commerce) Rules, 2020, continued unauthorized debits post-receipt of this revocation notice constitute unfair trade practice.

DEMAND & DIRECTIVE:
1. Immediately cease all automated debit requests against my card/bank/UPI account.
2. Confirm cancellation of the mandate and termination of future recurring debits in writing within 48 hours of receipt of this notice.
3. Note that any debit executed following this notice shall be treated as an unauthorized transaction and escalated immediately to the Reserve Bank of India (RBI) Ombudsman and the National Consumer Disputes Redressal Commission.

Sincerely,

{user_name}
Authorized Account Holder
"""

        # 2. Bank Revocation Instruction (Especially for NACH / Bank SI)
        bank_instruction = f"""FORMAL NOTICE TO ISSUING BANK / NODAL OFFICER
Date: {today_str}

To: The Branch Manager / Card Operations Division / Principal Nodal Officer
Subject: INSTRUCTION TO STOP PAYMENT AND REVOKE RECURRING MANDATE (REF: {ref_token})

Dear Sir / Madam,

I hereby instruct you to immediately stop and reject any future debit requests originating under the following mandate:

• Beneficiary / Merchant Name: {mandate.merchant_name}
• Mandate Reference (UMN / UMRN / Mandate ID): {ref_token}
• Payment Rail: {mandate.mandate_type}
• Account Number: {account_mask}
• Authorized Amount: INR {amt:,.2f} ({mandate.cadence})

Under RBI Master Circular on e-mandates and NACH Procedural Guidelines issued by NPCI, the customer is entitled to stop payments or withdraw a mandate by notifying the sponsor bank or destination bank.

Please confirm in writing that this mandate has been marked REVOKED on the bank's core banking system (CBS) and NPCI e-mandate hub.

Yours faithfully,

{user_name}
"""

        return {
            "mandate_id": mandate.id,
            "merchant_name": mandate.merchant_name,
            "ref_token": ref_token,
            "generated_date": today_str,
            "merchant_notice": {
                "subject": merchant_email_subject,
                "recipient": mandate.grievance_email or mandate.support_email or "support@merchant.com",
                "body": merchant_email_body.strip()
            },
            "bank_instruction": {
                "title": f"Bank Stop Payment Notice - {mandate.merchant_name}",
                "body": bank_instruction.strip()
            },
            "cancellation_steps": mandate.cancellation_steps or [],
            "cancellation_pitfall": mandate.pitfall or "Ensure you reach the final confirmation screen and save the cancellation ID."
        }

    @classmethod
    def build_revocation_deeplinks(cls, mandate: Mandate) -> Dict[str, Any]:
        """
        Generates platform deep-links to facilitate instant one-click cancellation.
        """
        rail = (mandate.mandate_type or "").upper()
        links = {
            "type": rail,
            "direct_portal_url": mandate.official_website or None,
            "app_deeplink": None,
            "instructions": ""
        }

        if "UPI" in rail:
            token = mandate.umn_or_umrn or mandate.id
            # Universal UPI Mandate Revoke URI scheme
            links["app_deeplink"] = f"upi://mandate/revoke?umn={token}"
            links["instructions"] = "Tap the link on mobile to open your default UPI app (GPay/PhonePe/Paytm) directly to the Mandate Revocation screen."
        elif "PLAY_STORE" in rail:
            links["direct_portal_url"] = "https://play.google.com/store/account/subscriptions"
            links["app_deeplink"] = "https://play.google.com/store/account/subscriptions"
            links["instructions"] = "Open Google Play Store -> Payments & Subscriptions -> Subscriptions -> Select Merchant -> Cancel."
        elif "APP_STORE" in rail:
            links["direct_portal_url"] = "https://apps.apple.com/account/subscriptions"
            links["app_deeplink"] = "itms-apps://apps.apple.com/account/subscriptions"
            links["instructions"] = "Open iOS Settings -> Tap your Name -> Subscriptions -> Select Merchant -> Cancel Subscription."
        elif "NACH" in rail or "BANK" in rail:
            links["direct_portal_url"] = "https://www.npci.org.in/what-we-do/nach/dispute-redressal-mechanism"
            links["instructions"] = "Submit the generated Stop Payment Notice to your bank branch or via NetBanking e-Mandates portal."

        return links

    @classmethod
    def get_escalation_pathway(cls, mandate: Mandate) -> List[Dict[str, Any]]:
        """
        Returns the statutory 4-tier escalation tree tailored to this mandate.
        """
        customized_chain = []
        for stage in ESCALATION_CHAIN:
            c = dict(stage)
            if c["tier"] == 1:
                c["specific_contact"] = mandate.grievance_email or mandate.support_email or "Merchant Support"
            elif c["tier"] == 2:
                c["specific_contact"] = "Issuing Bank Chargeback Desk"
            elif c["tier"] == 3:
                c["specific_contact"] = "Bank Principal Nodal Officer"
            elif c["tier"] == 4:
                c["specific_contact"] = "RBI Ombudsman (https://cms.rbi.org.in) / NCH 1915"
            customized_chain.append(c)

        return customized_chain

