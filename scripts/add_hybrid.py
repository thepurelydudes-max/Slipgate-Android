#!/usr/bin/env python3
"""Opt-in sing-box SOCKS5 hop and remote routing overlay, applied after all existing patches."""
from pathlib import Path
import argparse,shutil,xml.etree.ElementTree as ET

def one(p,old,new):
    s=p.read_text(encoding="utf-8")
    if s.count(old)!=1: raise RuntimeError("Upstream changed: "+str(p)+" "+old[:80])
    p.write_text(s.replace(old,new,1),encoding="utf-8")

def apply(android,root):
    base=android/"app/src/main"
    kotlin=base/"java/io/github/romanvht/byedpi"
    for name,dest in [("HybridProfiles.kt",kotlin/"services/HybridProfiles.kt"),
        ("HybridCore.kt",kotlin/"services/HybridCore.kt"),
        ("HybridSettingsActivity.kt",kotlin/"activities/HybridSettingsActivity.kt")]:
        shutil.copyfile(root/"hybrid"/name,dest)
    native=kotlin/"services/NativeSession.kt"
    one(native,'                createTunnel?.let { create ->',
        """                val hybridEnabled = if (createTunnel != null) withContext(Dispatchers.IO) {
                    HybridCore.start(service, config.host, config.port)
                } else false
                createTunnel?.let { create ->""")
    one(native,'                        appendLine("  address: ${config.host}")',
        '                        appendLine("  address: ${if (hybridEnabled) "127.0.0.1" else config.host}")')
    one(native,'                        appendLine("  port: ${config.port}")',
        '                        appendLine("  port: ${if (hybridEnabled) HybridProfiles.PORT else config.port}")')
    one(native,'                if (tunnelThread != null) TProxyService.stopTunnel()',
        '''                if (tunnelThread != null) TProxyService.stopTunnel()
                HybridCore.stop()''')
    one(native,'    private fun terminate() {',
        '''    private fun terminate() {
        HybridCore.stop()''')
    manifest=base/"AndroidManifest.xml"
    one(manifest,'        <activity\n            android:name=".activities.SettingsActivity"',
        '''        <activity android:name=".activities.HybridSettingsActivity"
            android:exported="false" android:label="SpeedFix / Гибрид" />
        <activity
            android:name=".activities.SettingsActivity"''')
    one(manifest,'android:allowBackup="true"','android:allowBackup="false"')
    main=kotlin/"activities/MainActivity.kt"
    one(main,'        if (item.itemId == 830043) {',
        '''        if (item.itemId == 830044) {
            startActivity(Intent(this, HybridSettingsActivity::class.java))
            return true
        }
        if (item.itemId == 830043) {''')
    one(main,'        menu?.add(Menu.NONE, 830043, Menu.NONE, "DPI: приложения и TCP/UDP")',
        '''        menu?.add(Menu.NONE, 830044, Menu.NONE, "SpeedFix / Гибридный режим")
            ?.setShowAsAction(MenuItem.SHOW_AS_ACTION_NEVER)
        menu?.add(Menu.NONE, 830043, Menu.NONE, "DPI: приложения и TCP/UDP")''')
    gradle=android/"app/build.gradle.kts"
    one(gradle,'val abis = setOf("armeabi-v7a", "arm64-v8a", "x86", "x86_64")','val abis = setOf("arm64-v8a")')
    one(gradle,'dependencies {',
        '''dependencies {
    implementation(files("libs/libbox.aar"))''')
    service=kotlin/"services/ByeDpiVpnService.kt"
    one(service,"        return START_NOT_STICKY","        return START_STICKY")
    ET.parse(manifest)
    print("Hybrid routes integrated, ByeDPI remains default.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--android",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    apply(a.android,a.root)
