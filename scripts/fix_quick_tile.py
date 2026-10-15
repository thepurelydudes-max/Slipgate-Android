#!/usr/bin/env python3
"""Give Slipgate one working QS tile with the Slipgate icon, wired to the main VPN.

Applied *after* the ByeByeDPI + Telegram upstream integrations.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

def one(path: Path, before: str, after: str) -> None:
    s = path.read_text(encoding="utf-8")
    if s.count(before) != 1:
        raise RuntimeError("Expected a single anchor in %s: %s" % (path, before[:80]))
    path.write_text(s.replace(before, after, 1), encoding="utf-8")

QUICK_TILE = """package io.github.romanvht.byedpi.services

import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import androidx.annotation.RequiresApi
import io.github.romanvht.byedpi.activities.MainActivity
import io.github.romanvht.byedpi.data.AppStatus
import io.github.romanvht.byedpi.data.Mode

/** Single Slipgate quick tile: always toggles the device-wide ByeDPI VPN, never proxy mode. */
@RequiresApi(Build.VERSION_CODES.N)
class QuickTileService : TileService() {
    companion object {
        private var instance: QuickTileService? = null
        fun updateTile() { instance?.updateStatus() }
    }

    override fun onStartListening() {
        super.onStartListening()
        instance = this
        ServiceManager.refresh(this)
        updateStatus()
    }

    override fun onStopListening() {
        instance = null
        super.onStopListening()
    }

    override fun onClick() {
        super.onClick()
        if (VpnService.prepare(this) != null) {
            // The system requires user approval; a background TileService cannot grant VPN consent.
            val launch = Intent(this, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                val pending = PendingIntent.getActivity(
                    this, 830044, launch, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                startActivityAndCollapse(pending)
            } else {
                @Suppress("DEPRECATION")
                startActivityAndCollapse(launch)
            }
            return
        }
        ServiceManager.toggleVpn(this)
    }

    private fun updateStatus() {
        val status = appStatus
        qsTile?.apply {
            state = if (status.first == AppStatus.Running && status.second == Mode.VPN)
                Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
            updateTile()
        }
    }
}
"""

def apply(android: Path, telegram: Path) -> None:
    root = android / "app/src/main"
    manifest = root / "AndroidManifest.xml"
    one(manifest,
        'android:name=".services.QuickTileService"\n            android:icon="@drawable/ic_notification"',
        'android:name=".services.QuickTileService"\n            android:icon="@drawable/slipgate_icon"')
    qs = root / "java/io/github/romanvht/byedpi/services/QuickTileService.kt"
    if not qs.exists():
        raise RuntimeError("ByeDPI QuickTileService missing")
    qs.write_text(QUICK_TILE, encoding="utf-8")

    manager = root / "java/io/github/romanvht/byedpi/services/ServiceManager.kt"
    one(manager, "    fun start(context: Context, mode: Mode) {",
'''    /**
     * A serialized click handler for the Quick Settings tile. refresh() is asynchronous,
     * so never read appStatus immediately after calling refresh() in the tile itself.
     */
    fun toggleVpn(context: Context) {
        val app = context.applicationContext as Application
        scope.launch {
            if (TestService.isRunning) return@launch
            restore(app)
            if (session?.mode == Mode.VPN) {
                waitStop()
            } else if (VpnService.prepare(app) == null) {
                waitStart(app, Mode.VPN)
            }
        }
    }

    fun start(context: Context, mode: Mode) {''')
    one(manager,
'''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) QuickTileService.updateTile()''',
'''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            QuickTileService.updateTile()
            // Refresh the icon/state even if Quick Settings was closed during the change.
            try {
                android.service.quicksettings.TileService.requestListeningState(
                    it, android.content.ComponentName(it, QuickTileService::class.java))
            } catch (_: Exception) {
                // Some OEMs restrict quick tile refresh requests.
            }
        }'''.replace("                    it, android.content.ComponentName(it, QuickTileService::class.java)", "                    application ?: return, android.content.ComponentName(application ?: return, QuickTileService::class.java)"))
    # The Telegram proxy remains in the app, but its second quick tile is intentionally removed.
    tg = telegram / "app/src/main/AndroidManifest.xml"
    tag = '''    <service android:name="dev.minios.tgwsproxy.service.ProxyTileService"
        android:exported="true" android:permission="android.permission.BIND_QUICK_SETTINGS_TILE">
      <intent-filter><action android:name="android.service.quicksettings.action.QS_TILE"/></intent-filter>
    </service>
'''
    one(tg, tag, "")
    ET.parse(manifest)
    ET.parse(tg)
    print("Slipgate VPN QS tile now has app icon, serialized toggle and permission handoff. Removed duplicate Telegram QS tile.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--android", required=True, type=Path)
    p.add_argument("--telegram", required=True, type=Path)
    a = p.parse_args()
    apply(a.android, a.telegram)
