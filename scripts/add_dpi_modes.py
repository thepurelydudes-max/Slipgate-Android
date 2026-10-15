#!/usr/bin/env python3
"""Slipgate UI for transport modes and TikTok targets, applied atop modern ByeByeDPI."""
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET

TIKTOK = """tiktok.com
www.tiktok.com
m.tiktok.com
vm.tiktok.com
vt.tiktok.com
tiktokv.com
tiktokcdn.com
tiktokcdn-us.com
tiktokcdn-eu.com
tiktokcdn-in.com
tiktokcdn-us.com
tiktokcdn.live
tiktokcdn.com
tiktokstaticb.com
tiktokstatic.com
byteoversea.com
ibytedtos.com
ibyteimg.com
muscdn.com
musical.ly
snssdk.com
isnssdk.com
byteimg.com
p16-sign.tiktokcdn-us.com
api2.musical.ly
api.tiktokv.com
log.tiktokv.com
"""

def one(file,old,new):
    text=file.read_text(encoding="utf-8")
    if text.count(old)!=1: raise RuntimeError("Unexpected upstream anchor: "+str(file)+" "+old)
    file.write_text(text.replace(old,new,1),encoding="utf-8")

def apply(android):
    root=android/"app/src/main"
    assets=root/"assets"
    assets.mkdir(exist_ok=True)
    (assets/"proxytest_tiktok.sites").write_text("\n".join(sorted(set(TIKTOK.split())))+"\n",encoding="utf-8")
    xml=root/"res/xml/main_settings.xml"
    old='    <androidx.preference.PreferenceCategory\n        android:title="@string/automation">'
    new='''    <androidx.preference.PreferenceCategory
        android:title="@string/slipgate_protocol_title">
        <ListPreference
            android:key="slipgate_protocol_mode"
            android:title="@string/slipgate_protocol_title"
            android:entries="@array/slipgate_protocol_labels"
            android:entryValues="@array/slipgate_protocol_values"
            android:summary="%s"
            android:defaultValue="auto" />
        <Preference
            android:key="slipgate_protocol_explainer"
            android:title="@string/slipgate_protocol_note"/>
    </androidx.preference.PreferenceCategory>

'''+old
    one(xml,old,new)
    resources=root/"res/values/slipgate_transport.xml"
    resources.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
<string name="slipgate_protocol_title">DPI: TCP / UDP</string>
<string name="slipgate_protocol_note">Changes take effect on reconnect. TCP only blocks UDP transport; this may break videos, games, calls or messaging. UDP enhancement is experimental and network-dependent.</string>
<string-array name="slipgate_protocol_labels">
    <item>Automatic — selected strategy</item>
    <item>TCP only — disable UDP completely</item>
    <item>TCP + UDP (QUIC) — add UDP desync stage</item>
</string-array>
<string-array name="slipgate_protocol_values">
    <item>auto</item><item>tcp</item><item>tcp_udp</item>
</string-array>
</resources>''',encoding="utf-8")
    ru=root/"res/values-ru"
    ru.mkdir(exist_ok=True)
    (ru/"slipgate_transport.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
<string name="slipgate_protocol_title">DPI: TCP / UDP</string>
<string name="slipgate_protocol_note">После смены режима переподключитесь. Режим TCP полностью отключает UDP и может нарушить воспроизведение видео, звонки и работу игр. UDP-обход экспериментальный.</string>
<string-array name="slipgate_protocol_labels">
    <item>Авто — выбранная стратегия</item>
    <item>Только TCP — UDP отключён</item>
    <item>TCP + UDP (QUIC) — добавить UDP-десинхронизацию</item>
</string-array>
</resources>''',encoding="utf-8")
    native=root/"java/io/github/romanvht/byedpi/services/NativeEngine.kt"
    one(native,
        '            val (defaultHost, defaultPort) = preferences.getProxyIpAndPort()',
        '''            val protocolMode = preferences.getString("slipgate_protocol_mode", "auto")
            val effectiveArgs = when (protocolMode) {
                "tcp" -> args.toList() + "--no-udp"
                "tcp_udp" -> args.toList() + listOf("-Ku", "-a3", "-An")
                else -> args.toList()
            }
            val (defaultHost, defaultPort) = preferences.getProxyIpAndPort()''')
    one(native,
        'val (host, port) = args.toList().checkIpAndPortInArgs()',
        'val (host, port) = effectiveArgs.checkIpAndPortInArgs()')
    one(native,
        '                args.toList(), host ?: defaultHost, (port ?: defaultPort).toInt(),',
        '                effectiveArgs, host ?: defaultHost, (port ?: defaultPort).toInt(),')
    # App selection already exists in ByeByeDPI settings (applist_type, selected_apps).
    # Provide direct entry for users in main menu.
    main=root/"java/io/github/romanvht/byedpi/activities/MainActivity.kt"
    one(main,
        '        if (item.itemId == 830042) {',
        '''        if (item.itemId == 830043) {
            startActivity(Intent(this, SettingsActivity::class.java))
            return true
        }
        if (item.itemId == 830042) {''')
    one(main,
        '        menu?.add(Menu.NONE, 830042, Menu.NONE, "Telegram MTProto / WS")',
        '''        menu?.add(Menu.NONE, 830043, Menu.NONE, "DPI: приложения и TCP/UDP")
            ?.setShowAsAction(MenuItem.SHOW_AS_ACTION_NEVER)
        menu?.add(Menu.NONE, 830042, Menu.NONE, "Telegram MTProto / WS")''')
    for path in (resources,ru/"slipgate_transport.xml",xml): ET.parse(path)
    print("Added TikTok targets, app selection menu, TCP/UDP preferences and active native-mode overrides")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--android",required=True,type=Path)
    a=parser.parse_args()
    apply(a.android)
