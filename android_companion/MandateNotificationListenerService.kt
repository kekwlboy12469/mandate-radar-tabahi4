package com.mandateradar.companion

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * 100% Google Play Policy Compliant Notification Listener.
 * Intercepts real-time financial debit and pre-debit notifications
 * from banking and UPI apps without requiring SMS permissions.
 */
class MandateNotificationListenerService : NotificationListenerService() {

    private val serviceScope = CoroutineScope(Dispatchers.IO)

    // Official package names of major Indian banking and UPI apps
    private val recognizedBankPackages = setOf(
        "com.google.android.apps.nbu.paisa.user", // Google Pay
        "com.phonepe.app",                       // PhonePe
        "net.one97.paytm",                       // Paytm
        "in.org.npci.upiapp",                    // BHIM UPI
        "com.hdfcbank.android",                  // HDFC Bank MobileBanking
        "com.sbi.lotusintouch",                  // YONO SBI
        "com.csam.icici.bank.imobile",           // ICICI iMobile Pay
        "com.axis.mobile",                       // Axis Mobile
        "com.msf.kopl",                          // Kotak 811
        "com.idfcfirstbank.optimus"              // IDFC FIRST Bank
    )

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn?.let { notification ->
            val packageName = notification.packageName ?: return
            if (!recognizedBankPackages.contains(packageName)) return

            val extras = notification.notification.extras
            val title = extras.getString("android.title") ?: ""
            val text = extras.getCharSequence("android.text")?.toString() ?: ""
            val fullText = "$title $text".trim()

            // Strict security filter: Never transmit OTPs or verification codes
            val lower = fullText.lowercase()
            if (lower.contains("otp") || lower.contains("verification code") || lower.contains("secret code")) {
                Log.d("MandateRadar", "Security: OTP notification dropped locally.")
                return
            }

            // Check if transactional or pre-debit
            val isFinancial = lower.contains("debited") || lower.contains("spent") ||
                              lower.contains("autopay") || lower.contains("mandate") ||
                              lower.contains("pre-debit") || lower.contains("paid")

            if (isFinancial) {
                serviceScope.launch {
                    MandateApiClient.sendNotificationPayload(
                        sender = packageName,
                        body = fullText,
                        timestamp = System.currentTimeMillis()
                    )
                }
            }
        }
    }
}

