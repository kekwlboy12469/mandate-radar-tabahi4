package com.mandateradar.companion

import android.util.Log
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * HTTP Client that communicates with Mandate Radar's API v1.
 */
object MandateApiClient {

    private const val BASE_URL = "http://10.0.2.2:8000/api/v1/integrations" // Local host or production domain
    private var deviceToken: String? = null

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    fun setDeviceToken(token: String) {
        this.deviceToken = token
    }

    suspend fun pairDevice(pin: String, deviceId: String, deviceName: String): Boolean {
        return try {
            val json = JSONObject().apply {
                put("pin", pin)
                put("device_id", deviceId)
                put("device_name", deviceName)
            }
            val body = json.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("$BASE_URL/sms/pair-verify")
                .post(body)
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val respJson = JSONObject(response.body?.string() ?: "{}")
                this.deviceToken = respJson.optString("pairing_token")
                true
            } else {
                false
            }
        } catch (e: Exception) {
            Log.e("MandateRadar", "Device pairing error: ${e.message}")
            false
        }
    }

    suspend fun sendNotificationPayload(sender: String, body: String, timestamp: Long) {
        try {
            val messageObj = JSONObject().apply {
                put("sender", sender)
                put("body", body)
                put("timestamp", java.time.Instant.ofEpochMilli(timestamp).toString())
            }
            val array = JSONArray().apply { put(messageObj) }
            val payload = JSONObject().apply {
                put("messages", array)
            }

            val requestBuilder = Request.Builder()
                .url("$BASE_URL/sms")
                .post(payload.toString().toRequestBody("application/json".toMediaType()))

            deviceToken?.let { token ->
                requestBuilder.header("Authorization", "Bearer $token")
            }

            val response = client.newCall(requestBuilder.build()).execute()
            Log.d("MandateRadar", "Payload dispatch response: ${response.code}")
        } catch (e: Exception) {
            Log.e("MandateRadar", "Failed to dispatch financial alert: ${e.message}")
        }
    }
}

