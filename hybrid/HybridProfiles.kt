package io.github.romanvht.byedpi.services

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Local-only encrypted subscription. No user credentials ship in the APK or build logs. */
object HybridProfiles {
    private const val ALIAS = "slipgate.speedfix.credentials.v1"
    private const val PREFS = "slipgate_hybrid_secrets"
    const val PORT = 10915
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getEntry(ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build())
        }.generateKey()
    }
    fun save(ctx: Context, profile: JSONObject) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val data = cipher.iv + cipher.doFinal(profile.toString().toByteArray(Charsets.UTF_8))
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString("blob", Base64.encodeToString(data, Base64.NO_WRAP)).apply()
    }
    fun load(ctx: Context): JSONObject? {
        val raw = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString("blob", null) ?: return null
        return try {
            val data = Base64.decode(raw, Base64.DEFAULT)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, data.copyOfRange(0,12)))
            JSONObject(String(cipher.doFinal(data.copyOfRange(12,data.size)), Charsets.UTF_8))
        } catch (_: Exception) { null }
    }
    fun outbound(ctx: Context): JSONObject? {
        val state = load(ctx) ?: return null
        if (!state.optBoolean("enabled", false)) return null
        val list = state.optJSONArray("nodes") ?: return null
        val idx = state.optInt("selected", -1)
        if (idx !in 0 until list.length()) return null
        return JSONObject(list.getJSONObject(idx).getJSONObject("outbound").toString())
            .put("tag", "speedfix")
    }
    fun domains(ctx: Context): List<String> {
        val manual = load(ctx)?.optString("domains", "").orEmpty()
            .lines().map { it.trim().lowercase().trimStart('.') }
            .filter { it.matches(Regex("[a-z0-9-]+(\\.[a-z0-9-]+)+")) }
        return (listOf("tiktok.com","tiktokv.com","tiktokcdn.com","tiktokcdn-us.com",
            "tiktokcdn-eu.com","tiktokstatic.com","tiktokstaticb.com","byteoversea.com",
            "ibytedtos.com","ibyteimg.com","byteimg.com","musical.ly","muscdn.com",
            "snssdk.com","isnssdk.com","chatgpt.com","openai.com",
            "oaistatic.com","oaiusercontent.com") + manual).distinct()
    }
    fun fetch(url: String): List<JSONObject> {
        require(url.startsWith("https://")) { "Нужна HTTPS-подписка" }
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.connectTimeout = 12000
        connection.readTimeout = 12000
        connection.setRequestProperty("User-Agent", "v2rayTun")
        try {
            require(connection.responseCode in 200..299) { "HTTP " + connection.responseCode }
            require(connection.url.protocol == "https") { "Запрещён переход на HTTP" }
            require(connection.contentLengthLong <= 4_194_304) { "Подписка слишком большая" }
            val bytes = connection.inputStream.use { input ->
                val out = java.io.ByteArrayOutputStream()
                val buf = ByteArray(8192)
                while (true) {
                    val n = input.read(buf)
                    if (n < 0) break
                    require(out.size() + n <= 4_194_304) { "Подписка слишком большая" }
                    out.write(buf, 0, n)
                }
                out.toByteArray()
            }
            return parse(String(bytes, Charsets.UTF_8))
        } finally { connection.disconnect() }
    }
    fun parse(raw: String): List<JSONObject> {
        val value = raw.trim().removePrefix("\uFEFF")
        if (value.startsWith("{")) {
            val arr = JSONObject(value).optJSONArray("outbounds")
                ?: throw IllegalArgumentException("Требуется список узлов")
            return (0 until arr.length()).mapNotNull { i ->
                val o = arr.optJSONObject(i) ?: return@mapNotNull null
                if (o.optString("type") !in listOf("vless","trojan","vmess","shadowsocks"))
                    return@mapNotNull null
                JSONObject().put("name",o.optString("tag","Server " + (i+1)))
                    .put("outbound",JSONObject(o.toString()))
            }.also { require(it.isNotEmpty()) { "Нет поддерживаемых узлов" } }.take(100)
        }
        val plain = if (value.startsWith("vless://") ||
            value.startsWith("trojan://") || value.startsWith("vmess://")) value
        else try {
            String(Base64.decode(value.replace("\n","").replace("\r",""),
                Base64.DEFAULT or Base64.URL_SAFE), Charsets.UTF_8)
        } catch (_: Exception) { value }
        return plain.lines().mapNotNull { try { node(it.trim()) } catch (_: Exception) { null } }
            .take(100).also { require(it.isNotEmpty()) {
                "Не найдены узлы VLESS/Trojan/VMess. Возможно, подписка возвращает Clash YAML."
            } }
    }
    private fun node(line: String): JSONObject? {
        if (line.startsWith("vmess://")) {
            val j = JSONObject(String(Base64.decode(line.substringAfter("://"),
                Base64.DEFAULT or Base64.URL_SAFE), Charsets.UTF_8))
            val server = j.getString("add")
            val o = JSONObject().put("type","vmess").put("server",server)
                .put("server_port",j.optString("port").toInt())
                .put("uuid",j.getString("id")).put("security",j.optString("scy","auto"))
                .put("alter_id",j.optString("aid","0").toIntOrNull() ?: 0)
            if (j.optString("tls") == "tls") o.put("tls",
                JSONObject().put("enabled",true).put("server_name",j.optString("sni",server)))
            if (j.optString("net") == "ws") o.put("transport", JSONObject()
                .put("type","ws").put("path",j.optString("path","/"))
                .put("headers",JSONObject().put("Host",j.optString("host",server))))
            return JSONObject().put("name",j.optString("ps",server)).put("outbound",o)
        }
        if (!line.startsWith("vless://") && !line.startsWith("trojan://")) return null
        val uri = URI(line.replace(" ", "%20"))
        val server = uri.host ?: return null
        if (uri.port !in 1..65535) return null
        val id = java.net.URLDecoder.decode(uri.rawUserInfo ?: return null, "UTF-8")
        val params = uri.rawQuery.orEmpty().split("&").mapNotNull {
            val q = it.split("=",limit=2)
            if (q.size == 2) java.net.URLDecoder.decode(q[0],"UTF-8") to
                java.net.URLDecoder.decode(q[1],"UTF-8") else null
        }.toMap()
        fun p(k: String): String = params[k].orEmpty()
        val o = JSONObject().put("type",uri.scheme).put("server",server)
            .put("server_port",uri.port)
        if (uri.scheme == "vless") {
            o.put("uuid",id)
            if (p("flow").isNotEmpty()) o.put("flow",p("flow"))
        } else o.put("password",id)
        if (p("security") in listOf("tls","reality") ||
            (uri.scheme == "trojan" && p("security") != "none")) {
            val tls = JSONObject().put("enabled",true)
                .put("server_name",p("sni").ifBlank { server })
            if (p("fp").isNotEmpty()) tls.put("utls",
                JSONObject().put("enabled",true).put("fingerprint",p("fp")))
            if (p("security") == "reality") tls.put("reality",JSONObject()
                .put("enabled",true).put("public_key",p("pbk")).put("short_id",p("sid")))
            if (p("alpn").isNotEmpty()) tls.put("alpn",JSONArray(p("alpn").split(",")))
            o.put("tls",tls)
        }
        val transport = when(p("type")) {
            "ws" -> JSONObject().put("type","ws").put("path",p("path").ifBlank { "/" })
                .put("headers",JSONObject().put("Host",p("host").ifBlank { server }))
            "grpc" -> JSONObject().put("type","grpc").put("service_name",p("serviceName"))
            else -> null
        }
        if (transport != null) o.put("transport",transport)
        return JSONObject().put("name",java.net.URLDecoder.decode(uri.rawFragment ?: server,"UTF-8"))
            .put("outbound",o)
    }
}
