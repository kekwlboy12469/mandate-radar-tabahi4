package com.mandateradar.companion

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Standard Telecommunication SMS BroadcastReceiver for Sideload / Direct APK mode.
 * Filters incoming SMS by Indian DLT sender IDs.
 */
class MandateSmsReceiver : BroadcastReceiver() {

    private val receiverScope = CoroutineScope(Dispatchers.IO)
    private val dltHeaderRegex = Regex("^[A-Za-z]{2}-[A-Za-z0-9]{6}$")

    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        for (sms in messages) {
            val sender = sms.originatingAddress ?: continue
            val body = sms.messageBody ?: continue

            // 1. DLT Header Validation (e.g. AX-HDFCBK, VM-SBIINB)
            if (!dltHeaderRegex.matches(sender)) {
                Log.d("MandateRadar", "Skipping non-DLT sender: $sender")
                continue
            }

            // 2. Strict OTP Discard
            val lower = body.lowercase()
            if (lower.contains("otp") || lower.contains("verification code") || lower.contains("do not share")) {
                Log.d("MandateRadar", "Security: OTP message dropped in RAM.")
                continue
            }

            // 3. Dispatch to Mandate Radar Webhook
            receiverScope.launch {
                MandateApiClient.sendNotificationPayload(
                    sender = sender,
                    body = body,
                    timestamp = sms.timestampMillis
                )
            }
        }
    }
}

