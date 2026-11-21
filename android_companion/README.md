# Mandate Radar - Android Companion Service
### Real-Time Financial Notification & SMS Synchronization Architecture

This companion module enables Mandate Radar to capture bank debits, UPI AutoPay activations, and pre-debit alerts directly from an authorized user's Android device.

---

## 1. Google Play Store Permission Strategy & Compliance

### The Constraint
Google Play Console policy explicitly restricts `READ_SMS` and `RECEIVE_SMS` permissions to default SMS handler applications. Personal finance apps that request SMS permissions risk immediate app suspension or rejection during store review.

### The Solution: Dual-Mode Architecture

| Feature | Mode 1: Notification Listener (Store Compliant) | Mode 2: SMS Receiver (Sideload / F-Droid) |
| :--- | :--- | :--- |
| **Android API** | `NotificationListenerService` | `BroadcastReceiver` (`SMS_RECEIVED`) |
| **Permissions** | `android.permission.BIND_NOTIFICATION_LISTENER_SERVICE` | `RECEIVE_SMS`, `READ_SMS` |
| **Play Store Review** | **100% Compliant** (Permitted for companion sync) | Restricted (Requires Enterprise / GitHub APK) |
| **Data Captured** | Bank push notifications (GPay, PhonePe, YONO, HDFC, etc.) | Telecommunication DLT SMS alerts |
| **OTP Leakage Risk** | Zero (Filtered in local RAM before dispatch) | Zero (Strict discard regex) |

---

## 2. Device Pairing Handshake (Zero Shared Passwords)

1. **User opens Mandate Radar Web Dashboard**:
   - Clicks *"Connect Android Device"*.
   - Dashboard calls `POST /api/v1/integrations/sms/pair-request`.
   - Server returns a 6-digit one-time PIN (e.g. `839102`), valid for 10 minutes.
2. **User enters PIN in Android App**:
   - Android App calls `POST /api/v1/integrations/sms/pair-verify`:
     ```json
     {
       "pin": "839102",
       "device_id": "android_99214a8f",
       "device_name": "Google Pixel 8 Pro"
     }
     ```
   - Server authenticates the PIN, creates/updates `IntegrationCredential`, and returns a persistent device JWT token `dev_tok_...`.
3. **Subsequent Sync**:
   - The Android app dispatches transactions or pre-debit notifications to:
     `POST /api/v1/integrations/sms`
     Header: `Authorization: Bearer dev_tok_...`

