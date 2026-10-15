#!/usr/bin/env python3
"""Integrate pinned MIT-licensed TgWsProxy Kotlin source into Slipgate APK."""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

def replace_one(path, original, replacement):
    text=path.read_text(encoding="utf-8")
    if text.count(original)!=1:
        raise RuntimeError("Expected exactly one patch anchor in "+str(path)+" "+original[:45])
    path.write_text(text.replace(original,replacement,1),encoding="utf-8")

def apply(android, tg):
    source=tg/"app"
    if not (source/"src/main/java/dev/minios/tgwsproxy/proxy/TgWsProxyServer.kt").is_file():
        raise RuntimeError("Expected pinned Telegram Kotlin source")
    (source/"build.gradle.kts").write_text("""
plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}
android {
    namespace = "dev.minios.tgwsproxy"
    compileSdk = 36
    defaultConfig { minSdk = 26 }
    buildFeatures { compose = true; buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlin { jvmToolchain(17) }
    lint {
        disable += setOf("CoroutineCreationDuringComposition", "StateFlowValueCalledInComposition")
    }
}
dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.04.01"))
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.9.4")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.4")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
""",encoding="utf-8")
    rootgradle=android/"build.gradle.kts"
    replace_one(rootgradle,
        'id("com.android.application") version "8.11.0" apply false',
        'id("com.android.application") version "8.11.0" apply false\n    id("com.android.library") version "8.11.0" apply false')
    replace_one(rootgradle,
        'id("org.jetbrains.kotlin.android") version "2.2.0" apply false',
        'id("org.jetbrains.kotlin.android") version "2.2.0" apply false\n    id("org.jetbrains.kotlin.plugin.compose") version "2.2.0" apply false\n    id("org.jetbrains.kotlin.plugin.serialization") version "2.2.0" apply false')
    with (android/"settings.gradle.kts").open("a",encoding="utf-8") as file:
        file.write('\ninclude(":telegram")\nproject(":telegram").projectDir = file("../telegram-upstream/app")\n')
    replace_one(android/"app/build.gradle.kts","dependencies {",'dependencies {\n    implementation(project(":telegram"))')
    manifest=source/"src/main/AndroidManifest.xml"
    manifest.write_text("""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-permission android:name="android.permission.INTERNET"/>
  <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>
  <uses-permission android:name="android.permission.WAKE_LOCK"/>
  <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
  <application>
    <activity android:name="dev.minios.tgwsproxy.ui.MainActivity"
        android:exported="false" android:theme="@style/Theme.TgWsProxy"/>
    <service android:name="dev.minios.tgwsproxy.service.ProxyService"
        android:exported="false" android:foregroundServiceType="specialUse">
      <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
          android:value="mtproto_proxy"/>
    </service>
    <service android:name="dev.minios.tgwsproxy.service.ProxyTileService"
        android:exported="true" android:permission="android.permission.BIND_QUICK_SETTINGS_TILE">
      <intent-filter><action android:name="android.service.quicksettings.action.QS_TILE"/></intent-filter>
    </service>
    <receiver android:name="dev.minios.tgwsproxy.service.BootReceiver"
        android:exported="false">
      <intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/></intent-filter>
    </receiver>
    <provider android:name="androidx.core.content.FileProvider"
        android:authorities="com.farliner.slipgate.android.fileprovider"
        android:exported="false" android:grantUriPermissions="true">
      <meta-data android:name="android.support.FILE_PROVIDER_PATHS"
          android:resource="@xml/file_paths"/>
    </provider>
  </application>
</manifest>""",encoding="utf-8")
    ui=android/"app/src/main/java/io/github/romanvht/byedpi/activities/MainActivity.kt"
    replace_one(ui,"override fun onOptionsItemSelected(item: MenuItem): Boolean {",
        """override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == 830042) {
            startActivity(Intent(this, dev.minios.tgwsproxy.ui.MainActivity::class.java))
            return true
        }""")
    replace_one(ui,"override fun onCreateOptionsMenu(menu: Menu?): Boolean {",
        """override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menu?.add(Menu.NONE, 830042, Menu.NONE, "Telegram MTProto / WS")
            ?.setShowAsAction(MenuItem.SHOW_AS_ACTION_NEVER)""")
    ET.parse(manifest)
    print("MTProto WS native Kotlin engine embedded with independent foreground service.")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--android",required=True,type=Path)
    parser.add_argument("--telegram",required=True,type=Path)
    args=parser.parse_args()
    apply(args.android,args.telegram)
