package io.github.romanvht.byedpi.services

import android.content.Context
import android.net.VpnService
import android.os.Build
import io.nekohasekai.libbox.CommandServer
import io.nekohasekai.libbox.CommandServerHandler
import io.nekohasekai.libbox.Libbox
import io.nekohasekai.libbox.OverrideOptions
import io.nekohasekai.libbox.PlatformInterface
import io.nekohasekai.libbox.SetupOptions
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.lang.reflect.Proxy

/**
 * An in-process SOCKS5 routing hop between HEV (TUN) and ByeDPI.
 * Only domains that match the opt-in exception list use the remote subscription node.
 * All other requests continue through the existing local ByeDPI SOCKS engine.
 *
 * The platform callback is intentionally narrow: there is no second TUN, polling,
 * background heartbeat or dedicated wake lock. Failure returns to ByeDPI-only mode.
 */
object HybridCore {
    private var server: CommandServer? = null
    private var initialized = false

    @Synchronized
    fun start(context: Context, dpiHost: String, dpiPort: Int): Boolean {
        stop()
        val remote = HybridProfiles.outbound(context) ?: return false
        val config = JSONObject()
            .put("log", JSONObject().put("level","warn"))
            .put("inbounds", JSONArray().put(JSONObject()
                .put("type","mixed").put("tag","local")
                .put("listen","127.0.0.1").put("listen_port",HybridProfiles.PORT)))
            .put("outbounds", JSONArray().put(JSONObject()
                .put("type","socks").put("tag","dpi")
                .put("server",when(dpiHost) {
                    "0.0.0.0" -> "127.0.0.1"
                    "::", "[::]" -> "::1"
                    else -> dpiHost
                })
                .put("server_port",dpiPort)).put(remote))
            .put("route",JSONObject()
                .put("rules",JSONArray()
                    .put(JSONObject().put("action","sniff")
                        .put("sniffer",JSONArray(listOf("http","tls","quic"))))
                    .put(JSONObject().put("domain_suffix",
                        JSONArray(HybridProfiles.domains(context)))
                        .put("outbound","speedfix")))
                .put("final","dpi"))
        try {
            if (!initialized) {
                val base = File(context.filesDir,"slipgate-libbox").apply { mkdirs() }
                val tmp = File(context.cacheDir,"slipgate-libbox").apply { mkdirs() }
                Libbox.setup(SetupOptions().apply {
                    basePath = base.absolutePath
                    workingPath = tmp.absolutePath
                    tempPath = tmp.absolutePath
                    commandServerListenPort = 0
                    crashReportSource = "slipgate"
                    appVersion = "400"
                    appMarketingVersion = "0.4.0"
                    logMaxLines = 100
                    debug = false
                    fixAndroidStack = true
                })
                initialized = true
            }
            Libbox.checkConfig(config.toString())
            val serverHandler = Proxy.newProxyInstance(
                CommandServerHandler::class.java.classLoader,
                arrayOf(CommandServerHandler::class.java)
            ) { _, method, _ ->
                when(method.name) {
                    "serviceStop","serviceReload","writeDebugMessage",
                    "setSystemProxyEnabled","triggerNativeCrash" -> null
                    "connectSSHAgent" -> -1
                    "getSystemProxyStatus" -> null
                    else -> defaultValue(method.returnType)
                }
            } as CommandServerHandler

            val platform = Proxy.newProxyInstance(
                PlatformInterface::class.java.classLoader,
                arrayOf(PlatformInterface::class.java)
            ) { _, method, args ->
                when(method.name) {
                    "usePlatformAutoDetectInterfaceControl" -> true
                    "autoDetectInterfaceControl" -> {
                        val fd = (args?.firstOrNull() as? Int) ?: -1
                        if (fd >= 0) (context as? VpnService)?.protect(fd)
                        null
                    }
                    "useProcFS" -> Build.VERSION.SDK_INT < Build.VERSION_CODES.Q
                    "openTun" -> -1 // This component never opens a second VPN interface.
                    "usePlatformBridge","usePlatformShell","underNetworkExtension",
                    "includeAllNetworks" -> false
                    else -> defaultValue(method.returnType)
                }
            } as PlatformInterface
            val candidate = CommandServer(serverHandler,platform)
            candidate.start()
            try {
                candidate.startOrReloadService(config.toString(),OverrideOptions())
            } catch (e: Exception) {
                candidate.close()
                throw e
            }
            server = candidate
            context.getSharedPreferences("slipgate_hybrid_status",Context.MODE_PRIVATE).edit()
                .putString("last_error","").apply()
            return true
        } catch (e: Exception) {
            // Do not expose user credentials or subscription links in logs.
            context.getSharedPreferences("slipgate_hybrid_status",Context.MODE_PRIVATE).edit()
                .putString("last_error","Маршрутизатор не запустился: " +
                    e.javaClass.simpleName).apply()
            return false
        }
    }
    @Synchronized
    fun stop() {
        val old = server
        server = null
        try { old?.close() } catch (_: Exception) { }
    }
    private fun defaultValue(type: Class<*>): Any? = when(type) {
        java.lang.Boolean.TYPE -> false
        java.lang.Integer.TYPE -> 0
        java.lang.Long.TYPE -> 0L
        java.lang.Float.TYPE -> 0f
        java.lang.Double.TYPE -> 0.0
        java.lang.Short.TYPE -> 0.toShort()
        java.lang.Byte.TYPE -> 0.toByte()
        else -> null
    }
}
